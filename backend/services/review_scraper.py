import asyncio
import datetime
import logging
from typing import List
from abc import ABC, abstractmethod
from google_play_scraper import reviews, Sort
from google_play_scraper.exceptions import NotFoundError

from models.review import ReviewRecord

logger = logging.getLogger(__name__)

class ReviewProvider(ABC):
    @abstractmethod
    async def get_reviews(self, app_id: str, start_date: datetime.datetime, end_date: datetime.datetime) -> List[ReviewRecord]:
        pass

class GooglePlayScraperProvider(ReviewProvider):
    async def get_reviews(self, app_id: str, start_date: datetime.datetime, end_date: datetime.datetime) -> List[ReviewRecord]:
        def fetch_sync():
            all_reviews = []
            seen_ids = set()
            continuation_token = None
            consecutive_zero_in_window = 0
            page_count = 0
            MAX_PAGES = 20

            while page_count < MAX_PAGES and consecutive_zero_in_window < 3:
                retries = 3
                delay = 2
                result = None
                while retries > 0:
                    try:
                        result, continuation_token = reviews(
                            app_id,
                            lang='en',
                            country='in',
                            sort=Sort.NEWEST,
                            count=200,
                            continuation_token=continuation_token
                        )
                        break
                    except NotFoundError:
                        raise ValueError(f"No reviews found for the specified period. Verify the app package ID and try again.")
                    except Exception as e:
                        retries -= 1
                        if retries == 0:
                            if '429' in str(e) or '403' in str(e):
                                if len(all_reviews) >= 10:
                                    logger.warning("Rate limited but returning existing reviews.")
                                    return all_reviews
                                raise RuntimeError("Unable to retrieve reviews — request was rate-limited. Please try again in a few minutes.")
                            raise RuntimeError("Unable to retrieve Google Play reviews. Check network connectivity or try again.")
                        import time
                        time.sleep(delay)
                        delay *= 2
                
                if not result:
                    break

                in_window_count = 0
                for r in result:
                    if r['reviewId'] in seen_ids:
                        continue
                    
                    seen_ids.add(r['reviewId'])
                    review_at = r.get('at')
                    if not review_at:
                        continue
                        
                    if isinstance(review_at, datetime.datetime):
                        if review_at.tzinfo is None:
                             review_at = review_at.replace(tzinfo=datetime.timezone.utc)
                    
                    if start_date <= review_at <= end_date:
                        in_window_count += 1
                        all_reviews.append(
                            ReviewRecord(
                                review_id=r['reviewId'],
                                review_text=r.get('content') or "",
                                rating=r.get('score', 0),
                                review_date=review_at.isoformat(),
                                app_version=r.get('reviewCreatedVersion') or "",
                                developer_reply=r.get('replyContent') or "",
                                source="Google Play",
                                source_url=""
                            )
                        )
                
                if in_window_count == 0:
                    consecutive_zero_in_window += 1
                else:
                    consecutive_zero_in_window = 0
                    
                page_count += 1
                if not continuation_token:
                    break
                    
            return all_reviews

        return await asyncio.to_thread(fetch_sync)
