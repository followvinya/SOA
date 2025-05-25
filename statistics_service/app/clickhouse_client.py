from clickhouse_driver import Client
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "9000"))
CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "statistics")


class ClickHouseClient:
    def __init__(self):
        self.client = Client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            database=CLICKHOUSE_DATABASE
        )
        self.init_database()

    def init_database(self):
        """Создаем базу данных и таблицы если их нет"""
        try:
            self.client.execute(f"CREATE DATABASE IF NOT EXISTS {CLICKHOUSE_DATABASE}")

            self.client.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_type String,
                    user_id UInt32,
                    post_id UInt32,
                    comment_id Nullable(UInt32),
                    timestamp DateTime,
                    date Date DEFAULT toDate(timestamp)
                ) ENGINE = MergeTree()
                PARTITION BY toYYYYMM(date)
                ORDER BY (event_type, post_id, timestamp)
            """)

            logger.info("ClickHouse database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ClickHouse: {str(e)}")

    def insert_event(self, event_type: str, user_id: int, post_id: int,
                     comment_id: int = None, timestamp: datetime = None):
        """Вставляем событие в ClickHouse"""
        if timestamp is None:
            timestamp = datetime.now()

        try:
            self.client.execute(
                """
                INSERT INTO events (event_type, user_id, post_id, comment_id, timestamp) 
                VALUES
                """,
                [(event_type, user_id, post_id, comment_id, timestamp)]
            )
        except Exception as e:
            logger.error(f"Error inserting event: {str(e)}")

    def get_post_stats(self, post_id: int):
        """Получаем статистику по посту"""
        query = """
        SELECT 
            countIf(event_type = 'view') as views_count,
            countIf(event_type = 'like') as likes_count,
            countIf(event_type = 'comment') as comments_count
        FROM events
        WHERE post_id = %(post_id)s
        """

        result = self.client.execute(query, {'post_id': post_id})
        if result:
            return {
                'views_count': result[0][0],
                'likes_count': result[0][1],
                'comments_count': result[0][2]
            }
        return {'views_count': 0, 'likes_count': 0, 'comments_count': 0}

    def get_post_dynamics(self, post_id: int, event_type: str,
                          start_date: str = None, end_date: str = None):
        """Получаем динамику событий по дням"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        query = """
        SELECT 
            toDate(timestamp) as date,
            count() as count
        FROM events
        WHERE post_id = %(post_id)s 
            AND event_type = %(event_type)s
            AND date >= %(start_date)s
            AND date <= %(end_date)s
        GROUP BY date
        ORDER BY date
        """

        result = self.client.execute(query, {
            'post_id': post_id,
            'event_type': event_type,
            'start_date': start_date,
            'end_date': end_date
        })

        return [{'date': str(row[0]), 'count': row[1]} for row in result]

    def get_top_posts(self, metric_type: str, limit: int = 10):
        """Получаем топ постов по метрике"""
        event_type_map = {
            'likes': 'like',
            'comments': 'comment',
            'views': 'view'
        }

        event_type = event_type_map.get(metric_type, 'view')

        query = """
        SELECT 
            post_id,
            count() as count
        FROM events
        WHERE event_type = %(event_type)s
        GROUP BY post_id
        ORDER BY count DESC
        LIMIT %(limit)s
        """

        result = self.client.execute(query, {
            'event_type': event_type,
            'limit': limit
        })

        return [{'post_id': row[0], 'count': row[1]} for row in result]

    def get_top_users(self, metric_type: str, limit: int = 10):
        """Получаем топ пользователей по метрике"""
        event_type_map = {
            'likes': 'like',
            'comments': 'comment',
            'views': 'view'
        }

        event_type = event_type_map.get(metric_type, 'view')

        query = """
        SELECT 
            user_id,
            count() as count
        FROM events
        WHERE event_type = %(event_type)s
        GROUP BY user_id
        ORDER BY count DESC
        LIMIT %(limit)s
        """

        result = self.client.execute(query, {
            'event_type': event_type,
            'limit': limit
        })

        return [{'user_id': row[0], 'count': row[1]} for row in result]