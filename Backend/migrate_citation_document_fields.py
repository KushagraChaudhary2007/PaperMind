import sqlite3
from pathlib import Path


DATABASE_PATH = (
    Path(__file__).resolve().parent
    / "papermind.db"
)


def main():
    if not DATABASE_PATH.exists():
        print(
            "papermind.db was not found."
        )

        return


    connection = sqlite3.connect(
        DATABASE_PATH
    )


    try:
        existing_columns = {
            row[1]

            for row in connection.execute(
                (
                    "PRAGMA table_info"
                    "(paper_citations)"
                )
            ).fetchall()
        }


        new_columns = {
            "document_type":
                "document_type VARCHAR(100)",

            "is_academic_publication":
                "is_academic_publication BOOLEAN",

            "citation_warning":
                "citation_warning TEXT",
        }


        added_columns = []


        for (
            column_name,
            column_definition,
        ) in new_columns.items():

            if (
                column_name
                in existing_columns
            ):
                print(
                    (
                        f"{column_name}: "
                        "already exists"
                    )
                )

                continue


            connection.execute(
                (
                    "ALTER TABLE "
                    "paper_citations "
                    "ADD COLUMN "
                    f"{column_definition}"
                )
            )

            added_columns.append(
                column_name
            )


        connection.commit()


        print()

        if added_columns:

            print(
                "Migration completed."
            )

            print(
                "Added columns:"
            )

            for column_name in (
                added_columns
            ):
                print(
                    f"- {column_name}"
                )

        else:

            print(
                (
                    "No migration was needed. "
                    "All columns already exist."
                )
            )


    except Exception as error:

        connection.rollback()

        print(
            "Migration failed:"
        )

        print(
            type(error).__name__,
            str(error),
        )

        raise


    finally:

        connection.close()


if __name__ == "__main__":
    main()