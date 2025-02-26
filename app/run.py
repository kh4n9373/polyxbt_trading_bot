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
    TAKE_PROFIT_THRESHOLD: float = 0.1
    STOP_LOSS_THRESHOLD: float = -0.2

@dataclass
class TradeData:
    prediction_id: str
    hash_id: str
    option_id: str
    entry_odds: List[float]
    prediction_idx: int
    max_profit: float
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
            logger.info(f'Event closed with profit {profit:.2%}, Position: {position}')
            print(f'Event closed with profit {profit:.2%}, Position: {position}')
            
        return profit

    async def get_current_odds(self, hash_id: str, option_id: str) -> List[float]:
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

        return [float(odd) for odd in json.loads(matching_opt['outcomePrices'])]

    async def record_tpsl_decision(
        self,
        trade: TradeData,
        profit: float,
        position: Position,
        decision: Optional[Decision] = None
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
                'entry_odds': trade.entry_odds,
                'curr_odds': trade.curr_odds,
                'max_profit': trade.max_profit,
                'tpsl_profit': profit,
                'tpsl_open_position': position.value,
                'tpsl_update_at': datetime.now().timestamp()
            }
        }
        
        if decision:
            document["$set"]['tpsl_decision'] = decision.value
            
        await self.mongo_client.update_one("tpsl_polyxbt",
                                                filter=filter, 
                                                data=document, 
                                                upsert=True)

    async def update_max_profit(
        self,
        prediction_id: str,
        max_profit: float
    ) -> None:
        """Update max profit in database."""
        await self.mongo_client.update_one(
            "tpsl_polyxbt",
            {"prediction_id": prediction_id},
            {'$set': {"max_profit": max_profit}}
        )

    async def evaluate_tpsl(self, trade: TradeData) -> Tuple[Position, Optional[Decision]]:
        """Evaluate whether to take profit or stop loss."""
        profit = self.calculate_profit(
            trade.entry_odds,
            trade.curr_odds,
            trade.prediction_idx
        )
        
        new_max_profit = max(trade.max_profit, profit)
        logger.info(f"Current profit: {profit:.2%}, Max profit: {new_max_profit:.2%}")
        print(f"Current profit: {profit:.2%}, Max profit: {new_max_profit:.2%}")
        if trade.curr_odds[0] == 1 or trade.curr_odds[1] == 1:
            if profit > 0:
                return Position.CLOSE, Decision.WIN
            else:
                return Position.CLOSE, Decision.LOSS
        if profit > 0 and new_max_profit - profit > self.config.TAKE_PROFIT_THRESHOLD:
            return Position.CLOSE, Decision.TAKE_PROFIT
        elif profit <= 0 and profit < self.config.STOP_LOSS_THRESHOLD:
            return Position.CLOSE, Decision.STOP_LOSS
        return Position.OPEN, None

    async def process_trade(self, trade: TradeData) -> bool:
        """Process a single trade with TPSL logic."""
        try:
            trade.curr_odds = await self.get_current_odds(trade.hash_id, trade.option_id)
            position, decision = await self.evaluate_tpsl(trade)
            curr_profit = self.calculate_profit(trade.entry_odds, 
                                                              trade.curr_odds, 
                                                              trade.prediction_idx)
            await self.record_tpsl_decision(trade, 
                                          curr_profit,
                                          position,
                                          decision)
            
            if position == Position.CLOSE:
                logger.info(f"Position closed: {decision.value}")
                print(f"Position closed: {decision.value}")
            else:
                logger.info("Position held")
                print("Position held")
                
            await self.update_max_profit(trade.prediction_id, 
                                       max(trade.max_profit, 
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
                    max_profit = tpsl_record.get('max_profit',0)
                    trade = TradeData(
                        prediction_id=prediction['prediction_id'],
                        hash_id=prediction['hash_id'],
                        option_id=prediction['detailed_prediction']['option_id'],
                        entry_odds=prediction['detailed_prediction']['odds'],
                        prediction_idx=prediction['detailed_prediction']['prediction_idx'],
                        max_profit=max_profit
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
    


