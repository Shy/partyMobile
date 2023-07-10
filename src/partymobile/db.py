from dotenv import load_dotenv
import os
import asyncpg


class Database:
    def __init__(self):
        load_dotenv()
        self.dsn = os.getenv("DATABASE_URL")
        self.pool = None
        self.superblocksURL = os.getenv("SUPERBLOCKS_URL")
        self.superblocksBearer = os.getenv("SUPERBLOCKS_BEARER")

    async def connect(self):
        """Initialize asyncpg Pool"""
        self.pool = await asyncpg.create_pool(dsn=self.dsn, min_size=2, max_size=4)

    async def getEvents(self):
        """Get all events"""
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM events order by date desc")

    async def refresh_attendee_table(self, event_id):
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                """SELECT attendee.attendee,
                        event_attendee_junction.rsvp,
                        event_attendee_junction.public_id,
                        event_attendee_junction.updated_at
                    from
                        event_attendee_junction join attendee
                    on
                        event_attendee_junction.attendee_id = attendee.id
                    where
                        event_attendee_junction.event_id =  $1
                    order by
                    event_attendee_junction.updated_at desc;""",
                event_id,
            )

    async def refresh_attendee_count(self, event_id):
        async with self.pool.acquire() as conn:
            response = await conn.fetch(
                """SELECT ea.rsvp,
                    COUNT(*) AS "rsvp_status"
                FROM
                    event_attendee_junction ea
                JOIN
                    attendee a ON ea.attendee_id = a.id
                WHERE
                    ea.event_id = $1
                    AND a.invited = true
                GROUP BY
                    ea.rsvp;""",
                event_id,
            )
            output = {"attending": 0, "maybe": 0, None: 0, "not_attending": 0}

            for row in response:
                output[row["rsvp"]] = row["rsvp_status"]
            return output
