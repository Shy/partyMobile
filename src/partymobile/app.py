"""
mobile app for party
"""
import json
import httpx
import toga
from toga.style import Pack
from toga import validators
from toga.style.pack import COLUMN, ROW, CENTER
from .db import Database
from .styles import Heading, SubBox, label, number_label, question_label, question


class partyMobile(toga.App):
    def create_main_box(self):
        self.main_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        welcome_heading = toga.Label(
            "Welcome back Shy!",
            style=Heading.style,
        )
        self.main_box.add(welcome_heading)
        self.main_box.add(
            toga.Divider(),
        )

        loadEventsButton = toga.Button(
            "Load Events", on_press=self.loadEvents, style=Pack(padding=5)
        )
        inviteFriendButton = toga.Button(
            "Invite new Friend", on_press=self.inviteFriend, style=Pack(padding=5)
        )
        self.main_box.add(loadEventsButton)
        self.main_box.add(inviteFriendButton)

    def create_invite_friend_box(self):
        welcome_heading = toga.Label(
            "Welcome to Shy.Party!",
            style=Heading.style,
        )
        nameLabel = toga.Label("What's your name?", style=question_label.style)
        self.nameInput = toga.TextInput(
            placeholder="Shy's Friend",
            style=question.style,
            validators=[validators.MinLength(3)],
        )
        dietLabel = toga.Label("Any Diterary Restrictions?", style=question_label.style)
        self.dietInput = toga.TextInput(
            placeholder="I must always be given ice cream.",
            style=question.style,
        )
        phoneLabel = toga.Label("What's your phone number?", style=question_label.style)
        self.phoneInput = toga.TextInput(
            value="+1",
            style=question.style,
            validators=[
                validators.MatchRegex(r"^\+[1-9]\d{10,10}$"),
            ],
        )
        inviteFriendButton = toga.Button(
            "Submit", on_press=self.addFriend, style=Pack(padding=5)
        )
        loadEventsButton = toga.Button(
            "Load Events", on_press=self.loadEvents, style=Pack(padding=5)
        )
        self.invite_box = toga.Box(
            style=Pack(
                direction=COLUMN,
            ),
            children=[
                welcome_heading,
                nameLabel,
                self.nameInput,
                dietLabel,
                self.dietInput,
                phoneLabel,
                self.phoneInput,
                inviteFriendButton,
                loadEventsButton,
            ],
        )

    async def addFriend(self, widget):
        async with httpx.AsyncClient(
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.Database.superblocksBearer}",
            }
        ) as client:
            response = await client.post(
                url=self.Database.superblocksURL,
                data=json.dumps(
                    {
                        "Diet": self.dietInput.value,
                        "Name": self.nameInput.value,
                        "Phone": self.phoneInput.value,
                    }
                ),
            )
        if response.status_code == 200:
            self.main_window.info_dialog(
                "Success",
                "You've been added! You should get a text invite to the next event in about 15 minutes.",
            )
        else:
            self.main_window.stack_trace_dialog(
                "Something went wrong",
                "Stack Trace for Shy",
                content=response,
            )

    def inviteFriend(self, widget):
        self.main_window.content = self.invite_box

    def create_event_box(self):
        self.event_box = toga.Box(
            style=Pack(
                direction=COLUMN,
            )
        )
        self.event_selector = toga.Selection(
            on_change=self.event_change,
            items=[],
            accessor="name",
            style=Pack(direction=ROW, padding=10, text_align=CENTER),
        )
        attendee_status_box = toga.Box(
            style=Pack(direction=ROW, padding=10, text_align=CENTER)
        )

        self.attending_Label = toga.Label("Going", style=label.style)
        self.attending_count = toga.Label("0", style=number_label.style)
        self.attending_count.style.color = "green"
        attending_box = toga.Box(
            style=SubBox.style,
            children=[self.attending_Label, self.attending_count],
        )
        not_attending_label = toga.Label("Can't Make it", style=label.style)
        self.not_attending_count = toga.Label(
            "0",
            style=number_label.style,
        )
        self.not_attending_count.style.color = "red"
        not_attending_box = toga.Box(
            style=SubBox.style,
            children=[not_attending_label, self.not_attending_count],
        )

        maybe_label = toga.Label("Maybe", style=label.style)
        self.maybe_count = toga.Label("0", style=number_label.style)
        self.maybe_count.style.color = "orange"
        maybe_box = toga.Box(
            style=SubBox.style,
            children=[maybe_label, self.maybe_count],
        )
        self.event_box.add(self.event_selector)
        attendee_status_box.add(attending_box)
        attendee_status_box.add(maybe_box)
        attendee_status_box.add(not_attending_box)

        self.attendee_table = toga.Table(
            ["Attendee", "Status", "Updated At"],
            style=Pack(flex=1, padding=10),
            missing_value="Yet to reply.",
            on_double_click=self.update_attendee_rsvp,
        )

        self.event_box.add(attendee_status_box)
        self.event_box.add(self.attendee_table)

    def update_attendee_rsvp():
        pass

    def startup(self):
        self.Database = Database()
        self.create_main_box()
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.main_box
        self.main_window.show()
        self.create_event_box()
        self.create_invite_friend_box()

    async def event_change(self, widget=None):
        event_id = self.event_selector.value
        self.attendee_table.data = []
        attendee_count = await self.Database.refresh_attendee_count(str((event_id.id)))
        attendee_info = await self.Database.refresh_attendee_table(str((event_id.id)))
        for attendee in attendee_info:
            self.attendee_table.data.append(
                [
                    attendee["attendee"],
                    attendee["rsvp"],
                    attendee["updated_at"].strftime("%m/%d %I:%M %p"),
                    attendee["public_id"],
                ]
            )

        self.attending_count.text = attendee_count["attending"]
        self.maybe_count.text = attendee_count["maybe"]
        self.not_attending_count.text = attendee_count["not_attending"]

    async def loadEvents(self, widget):
        progress = toga.ProgressBar(max=None, style=Pack(padding=10))
        progress.start()
        self.main_window.content = progress
        await self.Database.connect()
        events = await self.Database.getEvents()
        self.event_selector.items = []
        for event in events:
            self.event_selector.items.append(
                {"name": event["event"], "id": event["id"]}
            )
        await self.event_change()

        progress.stop()
        self.main_window.content = self.event_box


def main():
    return partyMobile(startup=partyMobile.startup)
