import requests
from dotenv import load_dotenv
load_dotenv() #環境変数のロード

from common.driver import *
from bs4 import BeautifulSoup as bs
from sqlalchemy.orm import Session

from common.database import SessionLocal, get_db
from models.item import *
from common.utility import print_query, get_domain
from config.const import *
from models.searched_item import *
from engine.amazon_sp_api import *

from common.logger import set_logger
logger = set_logger(__name__)

AMAZON_REVIEW_URL = "https://www.amazon.co.jp/product-reviews"

class AmazonCrawler():
    
    def fetch_soup(self, url:str, params:dict={}) -> bs:
        res = requests.get(url, headers=HEADER.GET, params=params)
        if not(300 > res.status_code >= 200):
            return None
        return bs(res.text, "html.parser")
    
    def fetch_item_review(self, jan:str):
        asin = fetch_asin_by_jan(jan)
        if asin == None:
            logger.error(f"asin not found:{jan}")
            return None
        soup = self.fetch_soup(f"{AMAZON_REVIEW_URL}/{asin}")
        
        title_elms = soup.select(".review-title-content")
        content_elms = soup.select(".review-text-content")
        star_elms = soup.select(".a-link-normal .a-icon-alt")
        posted_at_elms = soup.select("#cm_cr-review_list .review-date")

        review_items = []
        for title,content,star,posted_at in zip(title_elms,content_elms,star_elms,posted_at_elms):
            review_items.append(ReviewItem(title=title.text.replace('\n','')))
            review_items.append(ReviewItem(content=content.text.replace('\n','')))
            review_items.append(ReviewItem(star=star.string))
            review_items.append(ReviewItem(posted_at=posted_at.string))

        average_star = soup.select(".averageStarRating .a-icon-alt")
        average_star = average_star[0].string
        name = soup.select(".product-title")
        name = name[0].string

        return SearchedItem(asin=asin, jan=jan, name=name, average_star=average_star, review_items=review_items)
        