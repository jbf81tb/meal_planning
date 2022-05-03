import base64
from email.mime.text import MIMEText
import random
from pathlib import Path
THIS_PATH = Path(__file__).parent
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
sheets_creds = Credentials.from_authorized_user_file(THIS_PATH/'sheets_token.json', SHEETS_SCOPES)

GMAIL_SCOPES = ["https://mail.google.com/"]
gmail_creds = Credentials.from_authorized_user_file(THIS_PATH/'gmail_token.json', GMAIL_SCOPES)


SPREADSHEET_ID = '1o08n7AsRDTqLO12bYWLKnJr1bWQ-JgS83WcIsmkFjKc'
RANGE = 'Sheet1!B2:C'

RECENT_FOOD = THIS_PATH/'recent_meals.txt'
RECENT_GROUPS = THIS_PATH/'recent_groups.txt'


def get_spreadsheet_values() -> list[list[str, str]]:
    service = build('sheets', 'v4', credentials=sheets_creds)

    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE).execute()
    values = result.get('values', [])

    return values


def create_message(message_text, sender="jbf81tb@gmail.com", to="jbf81tb@gmail.com, kubevet@gmail.com", subject="meal planning"):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

  Returns:
    An object containing a base64url encoded email object.
  """
  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject
  return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}

def send_email(message):
    service = build('gmail', 'v1', credentials=gmail_creds)
    service.users().messages().send(userId="me", body=message).execute()


class foods:
    def __init__(self, values) -> None:
        self.values = values
        self._set_recent_food()
        self._set_recent_groups()
        self._set_possible_food()
        self.found_foods = []
        self.cleared_groups = False


    def _set_possible_food(self):
        self.possible_food = list(range(len(self.values)))
        random.shuffle(self.possible_food)


    def _set_recent_food(self) -> list[str]:
        with open(RECENT_FOOD) as f:
            txt = f.read()
        self.recent_foods = txt.split('\n')

    def _set_recent_groups(self) -> list[str]:
        with open(RECENT_GROUPS) as f:
            txt = f.read()
        self.recent_groups = txt.split('\n')



    def print_foods(self, food, group):
        # print(food, ' - ', group)
        with open(RECENT_FOOD, 'a') as f:
            f.write(food+'\n')
        with open(RECENT_GROUPS, 'a') as f:
            f.write(group+'\n')
        self.recent_foods.append(food)
        self.recent_groups.append(group)
        self.found_foods.append(food)

    def clear_groups(self):
        with open(RECENT_GROUPS, 'w') as f:
            f.write('')
        self._set_recent_groups()
        self._set_possible_food()
        self.cleared_groups = True

    def clear_foods(self):
        with open(RECENT_FOOD, 'w') as f:
            f.write('')
        self._set_recent_food()
        self._set_possible_food()

    def _try_to_find_food(self):
        i = self.possible_food.pop()

        food, group = self.values[i]

        if (food in self.recent_foods) or (group in self.recent_groups): 
            return
        else:
            f.print_foods(food, group)

    def try_to_find_foods(self, num=4):
        while len(self.found_foods)<num:
            try:
                self._try_to_find_food()
            except IndexError:
                if self.cleared_groups:
                    self.clear_foods()
                else:
                    self.clear_groups()






if __name__ == '__main__':
    values = get_spreadsheet_values()
    f = foods(values)
    f.try_to_find_foods()
    print("\n".join(f.found_foods))
    send_email(create_message("\n".join(f.found_foods)))
