import json
import sqlite3

from src.services.llm.chat_history import ChatHistory


class ChatDB:
    def __init__(self, db_path: str = "data/chats/chats.db") -> None:
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS chats (
        chat_id TEXT PRIMARY KEY,
        history TEXT
        )
        """
        )
        self.conn.commit()

    def get_chat(self, chat_id: str) -> ChatHistory:
        cursor = self.conn.cursor()
        cursor.execute("SELECT history FROM chats WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        if row:
            history = json.loads(row[0])
            return ChatHistory(history)
        return ChatHistory()

    def save_chat(self, chat_id: str, history: ChatHistory) -> None:
        cursor = self.conn.cursor()
        history_json = json.dumps(history.history, ensure_ascii=False)
        cursor.execute(
            "REPLACE INTO chats (chat_id, history) VALUES (?, ?)",
            (chat_id, history_json),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


if __name__ == "__main__":
    db = ChatDB()
    chat = ChatHistory()
    chat.add_user_message("Привет!")
    chat.add_assistant_message("Здравствуйте, чем могу помочь?")
    db.save_chat("chat1", chat)
    restored = db.get_chat("chat1")
    print(restored.history)
    db.close()
