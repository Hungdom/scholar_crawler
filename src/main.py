from src.crawler.scholar_crawler import ScholarCrawler
from src.crawler.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    try:
        logger.info("Starting math papers crawler...")
        crawler = ScholarCrawler()
        stored_count = crawler.crawl_math_papers()
        logger.info(f"Crawling completed successfully! Stored {stored_count} papers.")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main() 