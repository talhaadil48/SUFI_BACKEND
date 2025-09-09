class NotificationQueries:
    def __init__(self, conn):
        self.conn = conn

    def create_notification(self, title, message, target_type, target_user_ids=None):
        query = """
        INSERT INTO notifications (title, message, target_type, target_user_ids)
        VALUES (%s, %s, %s, %s)
        RETURNING id, title, message, target_type, target_user_ids, created_at;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (title, message, target_type, target_user_ids))
            notification = cur.fetchone()
            self.conn.commit()
        return notification

    def get_user_notifications(self, user_id):
        user = self.get_user_by_id(user_id)
        if not user or user["role"] == "admin":
            return []

        user_role = user["role"]+'s'  # Convert 'writer' to 'writers', 'vocalist' to 'vocalists'

        query = """
        SELECT n.id, n.title, n.message, n.target_type, n.target_user_ids, n.created_at,
            CASE WHEN nr.id IS NULL THEN FALSE ELSE TRUE END AS is_read
        FROM notifications n
        LEFT JOIN notification_reads nr
            ON nr.notification_id = n.id AND nr.user_id = %s
        WHERE n.target_type = 'all'
        OR n.target_type = %s
        OR (n.target_type = 'specific' AND %s = ANY(n.target_user_ids))
        ORDER BY n.created_at DESC;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (user_id, user_role, user_id))
            notifications = cur.fetchall()
        return notifications

    def mark_as_read(self, notification_id, user_id):
        query = """
        INSERT INTO notification_reads (notification_id, user_id)
        VALUES (%s, %s)
        ON CONFLICT (notification_id, user_id) DO NOTHING
        RETURNING id;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (notification_id, user_id))
            read_entry = cur.fetchone()
            self.conn.commit()
        return read_entry
