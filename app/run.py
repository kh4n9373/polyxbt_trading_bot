from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import json
import logging
import asyncio
from enum import Enum

from app.database.mongodb import AsyncMongoManager
from app.constants.database import (
    DISTILLED_DATABASE_NAME, 
    DISTILLED_TEST_DATABASE_NAME
)
from app.config import settings
from app.utils.discord import sent_poly_win_loss_discord

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Position(str, Enum):
    OPEN = "OPEN"
    CLOSE = "CLOSE"

class Decision(str, Enum):
    TAKE_PROFIT = "TAKE PROFIT"
    STOP_LOSS = "STOP LOSS"
    LOSS = "LOSS"
    WIN = "WIN"
    HOLD = "HOLD"

@dataclass
class TradingConfig:
    TAKE_PROFIT_THRESHOLD: float = 0.5
    STOP_LOSS_THRESHOLD: float = 2/5

@dataclass
class TradeData:
    prediction_id: str
    prediction: str
    hash_id: str
    option_id: str
    entry_odds: List[float]
    prediction_idx: int
    highest_profit: float
    volume: float
    created_at: int
    option: str
    curr_odds: Optional[List[float]] = None

class TradingBot:
    def __init__(
        self,
        main_client: AsyncMongoManager,
        test_client: AsyncMongoManager,
        config: TradingConfig
    ):
        self.mongo_client = main_client
        self.test_mongo_client = test_client
        self.config = config
        
    @staticmethod
    def calculate_profit(
        entry_odds: List[float],
        curr_odds: List[float],
        prediction_idx: int
    ) -> float:
        """Calculate profit percentage for a given position."""
        if not (0 <= prediction_idx < len(entry_odds)):
            raise ValueError(f"Invalid prediction_idx: {prediction_idx}")
            
        profit = (curr_odds[prediction_idx] - entry_odds[prediction_idx]) / entry_odds[prediction_idx]
        
        if 1 in curr_odds:
            position = 'WIN' if curr_odds[prediction_idx] == 1 else 'LOSS'
            # logger.info(f'Event closed with profit {profit:.2%}, Position: {position}')
            print(f'Event closed with profit {profit:.2%}, Position: {position}')
            
        return profit

    async def get_outcome_prices_text(self, entry_odds : list, prediction_idx: int):
        outcome_prices_text = f"{entry_odds}, means having {round(entry_odds[prediction_idx]*100, 2)}% chance of winning ${(1-entry_odds[prediction_idx])/entry_odds[prediction_idx]} for every $1"
        return outcome_prices_text
    
    async def get_current_odds(self,trade: TradeData, hash_id: str, option_id: str) -> List[float]:
        """Fetch current odds from the database."""
        event = await self.mongo_client.find_one(
            settings.poly_events_collection_name,
            {"hash_id": hash_id}
        )
        if not event:
            raise ValueError(f"Event not found for hash_id: {hash_id}")

        matching_opt = next(
            (opt for opt in event['markets'] if str(opt['id']) == str(option_id)),
            None
        )
        if not matching_opt:
            raise ValueError(f"Option not found for option_id: {option_id} for event {hash_id}")
        trade.option = matching_opt['question']
        return [float(odd) for odd in json.loads(matching_opt['outcomePrices'])]

    async def record_tpsl_decision(
        self,
        trade: TradeData,
        profit: float,
        position: Position,
        decision: Optional[Decision] = None,
        send_discord: bool = False
    ) -> None:
        """Record TPSL decision in database."""
        filter = {
            'hash_id': trade.hash_id,
            'prediction_id': trade.prediction_id,
            'option_id': trade.option_id,
        }
        document = {
            "$set":{
                'hash_id': trade.hash_id,
                'prediction_id': trade.prediction_id,
                'option_id': trade.option_id,
                'created_at': trade.created_at,
                'entry_odds': trade.entry_odds,
                'curr_odds': trade.curr_odds,
                'highest_profit': trade.highest_profit,
                'tpsl_profit': profit,
                'tpsl_open_position': position.value,
                'tpsl_update_at': datetime.now().timestamp(),
                'tpsl_decision': decision.value,
                'volume':trade.volume
            }
        }
        
        # send to discord
        event = await self.mongo_client.find_one(
            settings.poly_events_collection_name,
            {"hash_id": trade.hash_id}
        )
        if decision.value not in ["HOLD"] and trade.volume > 100_000 and send_discord:
                sent_poly_win_loss_discord(
                    f"""- Hash ID: {trade.hash_id}
- Prediction ID: {trade.prediction_id}
- Title: {event['title']}
- URL: {"https://polymarket.com/event/" + event['slug']}
- Option: `{trade.option}`
- Prediction: `{trade.prediction}`
- Entry Timing: `{trade.created_at}`
- Outcome Prices: `{await self.get_outcome_prices_text(trade.entry_odds,trade.prediction_idx)}`
- Volume: `{trade.volume}`
- Win/Loss: `{decision.value}`
- Profit: `${profit}`
"""
                )
        await self.mongo_client.update_one("tpsl_polyxbt",
                                                filter=filter, 
                                                data=document, 
                                                upsert=True)
    async def update_highest_profit(
        self,
        prediction_id: str,
        highest_profit: float
    ) -> None:
        """Update max profit in database."""
        await self.mongo_client.update_one(
            "tpsl_polyxbt",
            {"prediction_id": prediction_id},
            {'$set': {"highest_profit": highest_profit}}
        )

    async def evaluate_tpsl(self, trade: TradeData) -> Tuple[Position, Optional[Decision]]:
        """Evaluate whether to take profit or stop loss."""
        profit = self.calculate_profit(
            trade.entry_odds,
            trade.curr_odds,
            trade.prediction_idx
        )
        
        new_highest_profit = max(trade.highest_profit, profit)
        logger.info(f"Current profit: {profit:.2%}, Max profit: {new_highest_profit:.2%}")
        print(f"Current profit: {profit:.2%}, Max profit: {new_highest_profit:.2%}")
        if trade.curr_odds[0] == 1 or trade.curr_odds[1] == 1:
            if profit > 0:
                return Position.CLOSE, Decision.WIN
            else:
                return Position.CLOSE, Decision.LOSS
        
        # max_profit: trần profit
        max_profit = (1-trade.entry_odds[trade.prediction_idx])/trade.entry_odds[trade.prediction_idx]

        if profit > min(0.2, 0.5*max_profit) and (new_highest_profit - profit)/new_highest_profit > self.config.TAKE_PROFIT_THRESHOLD:
            return Position.CLOSE, Decision.TAKE_PROFIT
        
        elif profit <= 0 and abs(profit/max_profit) > self.config.STOP_LOSS_THRESHOLD:
            return Position.CLOSE, Decision.STOP_LOSS
        
        return Position.OPEN, Decision.HOLD

    async def process_trade(self, trade: TradeData) -> bool:
        """Process a single trade with TPSL logic."""
        try:
            trade.curr_odds = await self.get_current_odds(trade,trade.hash_id, trade.option_id)
            position, decision = await self.evaluate_tpsl(trade)
            curr_profit = self.calculate_profit(trade.entry_odds, 
                                                              trade.curr_odds, 
                                                              trade.prediction_idx)
            await self.record_tpsl_decision(trade, 
                                          curr_profit,
                                          position,
                                          decision,
                                          send_discord=True)
            
            if position == Position.CLOSE:
                # logger.info(f"Position closed: {decision.value}")
                print(f"Position closed: {decision.value}")
            else:
                # logger.info("Position held")
                print("Position held")
                
            await self.update_highest_profit(trade.prediction_id, 
                                       max(trade.highest_profit, 
                                           curr_profit))
            return True
            
        except Exception as e:
            logger.error(f"Error processing trade: {str(e)}", exc_info=True)
            return False

    async def run(self) -> None:
        """Main entry point to process all open trades."""
        try:
            predictions = await self.mongo_client.find(
                settings.poly_predictions_collection_name,
                {
                    "open_position": {
                        "$exists": True
                    }
                    # "open_position":"CLOSE"
                }
            )

            for prediction in predictions:
                # Check xem tpsl da close position cho predicion nay chua
                tpsl_record = await self.mongo_client.find_one(
                    "tpsl_polyxbt",
                    {
                        "prediction_id":prediction["prediction_id"],
                        "tpsl_open_position": 'CLOSE'
                    }
                )
                if not tpsl_record:
                    tpsl_record = await self.mongo_client.find_one(
                        "tpsl_polyxbt",
                        {
                            "prediction_id":prediction["prediction_id"],
                        }
                    )
                    if not tpsl_record: tpsl_record = {}
                    highest_profit = tpsl_record.get('highest_profit',0)
                    trade = TradeData(
                        prediction_id=prediction['prediction_id'],
                        prediction = prediction['detailed_prediction']['prediction'],
                        hash_id=prediction['hash_id'],
                        option_id=prediction['detailed_prediction']['option_id'],
                        entry_odds=prediction['detailed_prediction']['odds'],
                        prediction_idx=prediction['detailed_prediction']['prediction_idx'],
                        volume=prediction["volume"],
                        created_at=prediction["created_at"],
                        option="",
                        highest_profit=highest_profit
                    )
                    
                    await self.process_trade(trade)
                
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}", exc_info=True)
async def run_cron_job():
    config = TradingConfig()
    main_client = AsyncMongoManager(DISTILLED_DATABASE_NAME)
    test_client = AsyncMongoManager(DISTILLED_TEST_DATABASE_NAME)
    bot = TradingBot(main_client, test_client, config)

    await bot.run()
    


