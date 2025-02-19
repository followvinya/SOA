erDiagram
    USERS {
        int id PK
        string email
        string password_hash
        string username
        string full_name
        date registered_at
    }

    ROLES {
        int id PK
        string role_name
        string description
        date created_at
        date updated_at
    }

    USER_ROLES {
        int id PK
        int user_id FK
        int role_id FK
        date assigned_at
        bool is_active
    }

    USERS ||--o{ USER_ROLES : "has"
    ROLES ||--o{ USER_ROLES : "can be assigned"



erDiagram

    POSTS {
        int id PK
        int author_id
        string title
        string content
        date created_at
        date updated_at
    }

    COMMENTS {
        int id PK
        int post_id FK
        int author_id
        int parent_comment_id FK "nullable"
        string text
        date created_at
        date updated_at
    }

    POST_ATTACHMENTS {
        int id PK
        int post_id FK
        string file_url
        string file_type
        double file_size
        string description
        date created_at
    }

    POSTS ||--o{ COMMENTS : "can have"
    COMMENTS ||--o{ COMMENTS : "reply to"
    POSTS ||--o{ POST_ATTACHMENTS : "can have"


erDiagram

    EVENTS_LOG {
        int  event_id PK
        string entity_type    "POST, COMMENT, и т.д."
        int entity_id
        int user_id
        string  event_type     "LIKE, VIEW, COMMENT"
        datetime created_at
    }

    DAILY_STATS {
        int id PK
        date  stat_date
        string  entity_type
        int  entity_id
        int likes_count
        int  views_count
        int comments_count
        datetime updated_at
    }

    MONTHLY_STATS {
        int  id PK
        string  year_month      "YYYY-MM"
        string  entity_type
        int entity_id
        int likes_count
        int views_count
        int comments_count
        datetime updated_at
    }

    EVENTS_LOG ||..|| DAILY_STATS : "aggregated into"
    EVENTS_LOG ||..|| MONTHLY_STATS : "aggregated into"