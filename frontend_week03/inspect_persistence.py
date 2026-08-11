"""Inspect the Week 2 ORM mappings without connecting to a database."""

from src.financeai.week02_persistence import ConversationRecord, MessageRecord


def main() -> None:
    print("Conversation table:", ConversationRecord.__tablename__)
    print("Message table:", MessageRecord.__tablename__)
    print("Conversation columns:", sorted(ConversationRecord.__table__.columns.keys()))
    print("Message columns:", sorted(MessageRecord.__table__.columns.keys()))


if __name__ == "__main__":
    main()
