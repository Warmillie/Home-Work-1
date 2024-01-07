# tsamsing change
from collections import UserDict
from datetime import datetime
import cmd
import pickle
from pathlib import Path
from typing import List
from abc import ABC, abstractmethod
import sys
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.validation import Validator, ValidationError
from rich.console import Console
from rich.table import Table
import re
from .sort_files import run
console = Console()
COMMANDS = {'add_name': ['add_name', 'Додавання нового контакту у довідник'],
            'add_phone': ['add_phone Name', 'Додавання телефонного номеру до контакту Name.\nКожен контакт може мати кілька номерів'],
            'add_birthday': ['add_birthday Name', 'Додавання для контакта Name дня народження у форматі РРРР-ММ-ДД.\nКожен контакт має тільки один день народження.\nТакож застосовується для зміни дня народження'],
            'add_email': ['add_email Name', 'Додавання адреси електроної пошти для контакта Name.\nКожен контакт має тільки один e-mail.\nТакож застосовується для зміни e-mail'],
            'add_address': ['add_address Name', 'Додавання адреси для контакта Name.\nКожен контакт має тільки одну адресу.\nТакож застосовується для зміни адреси'],            
}
class Field:
    def __init__(self, value):
        self._value = None
        self.value = value
    @property
    def value(self):
        return self._value
    @value.setter
    def value(self, new_value):
        self._value = new_value
    def __str__(self):
        return str(self._value)
    def validate(self):
        pass
class Name(Field):
    def __init__(self, name):
        super().__init__(name)
class Phone(Field):
    def validate(self):
        if self._value and not (isinstance(self._value, str) and len(self._value) == 10 and self._value.isdigit()):
            raise ValueError("Phone must be a 10-digit number.")
    @Field.value.setter
    def value(self, new_value):
        if not isinstance(new_value, str) or not new_value.isdigit():
            raise ValueError("Phone must be a string containing only digits.")
        self._value = new_value
        self.validate()
class Address(Field):
    def __init__(self, value):
        super().__init__(value)
class Email(Field):
    @Field.value.setter
    def value(self, new_value):
        result = re.findall(r"[a-zA-Z0-9_.]+@\w+\.\w{2,3}", new_value)
        try:
            self._value = result[0]
        except IndexError:
            raise IndexError("E-mail must be 'name@domain'")
class Birthday(Field):
    @Field.value.setter
    def value(self, new_value):
        try:
            datetime.strptime(new_value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format!!! Use YYYY-MM-DD.")

        self._value = new_value
class Record:
    def __init__(self, name, email=None, address=None, birthday=None):
        self.name = Name(name)
        self.phones = []
        self.email = Email(email) if email else None
        self.address = Address(address) if address else None
        self.birthday = Birthday(birthday) if birthday else None
    def add_phone(self, phone):
        phone_field = Phone(phone)
        phone_field.validate()
        self.phones.append(phone_field)
    def add_email(self, email):
        email_field = Email(email)
        self.email = email_field
    def delete_email(self):
        self.email = None
    def add_address(self, address):
        address_field = Address(address)
        self.address = address_field
    def delete_address(self):
        self.address = None
    def add_birthday(self, birthday):
        new_birthday = Birthday(birthday)
        self.birthday = new_birthday
    def remove_phone(self, phone):
        pass
    def edit_phone(self, old_phone, new_phone):
        pass
    def find_phone(self, phone):
        pass
    def __str__(self):
        return f"Record(name={self.name.value}, birthday={self.birthday}, phones={[phone.value for phone in self.phones]})"
    def days_to_birthday(self):
        pass
class AddressBook(UserDict):
    record_id = None
    def __init__(self, file="adress_book_1.pkl"):
        self.file = Path(file)
        self.record_id = 0
        self.record = {}
        super().__init__()
    def add_record(self, record):
        self.data[record.name.value] = record
    def find(self, term):
        if term in self.data:
            return self.data[term]
        else:
            return None
    def delete_record(self, name):
        if name.name.value in self.data:
            del self.data[name.name.value]
    def iterator(self, item_number):
        pass
    def dump(self):
        with open(self.file, "wb") as file:
            pickle.dump((self.record_id, dict(self.data)), file)
    def load(self):
        if not self.file.exists():
            return
        with open(self.file, "rb") as file:
            self.record_id, data = pickle.load(file)
            self.data.update(data)
    def find_by_term(self, term: str) -> List[Record]:
        pass
class Note(Field):
    def __init__(self, text, date, tags=None):
        super().__init__(text)
        self.tags = tags if tags is not None else []
        self.date = date
    def add_tag(self, tag):
        self.tags.append(tag)
    def remove_tag(self, tag):
        self.tags.remove(tag)
class NoteRecord(Record):
    def __init__(self, name, birthday=None):
        super().__init__(name, birthday=None)
        self.notes = []
    def add_note(self, text, tags=None):
        now = datetime.now()
        date = now.strftime("%Y-%m-%d %H:%M:%S")
        note = Note(text, date, tags)
        self.notes.append(note)
    def remove_note(self, text):
        if not text:
            raise ValueError("Введіть нотаток!")
        self.notes = [note for note in self.notes if note.value != text]
    def edit_note(self, new_text, new_tags=None):
        pass
    def find_notes_by_tag(self, tag):
        return [note for note in self.notes if tag in note.tegs]  
    def find_notes_by_term(self, term):
        return [note for note in self.notes if term.lower() in note.value.lower() or any(term.lower() in tag.lower() for tag in note.tags)]
    def __str__(self):
        notes_str = " | ".join([f"{note.value} [{' ,'.join(note.tags)}]" for note in self.notes])
        return f"NoteRecord(name={self.name.value}, notes={notes_str})"
class Controller():
    def __init__(self):
        super().__init__()
        self.book = AddressBook()

    def do_exit(self):
        self.book.dump()
        print("Адресна книга збережена! Вихід...")
        return True

    def do_save(self):
        self.book.dump()
        print("Адресна книга збережена!")

    def do_load(self):
        self.book.load()
        print("Адресна книга відновлена")

    def do_help(self):
        table = Table(show_header=True, header_style="bold blue", border_style='bold green')
        table.add_column('Синтаксис команди')
        table.add_column('Опис')

        for commands in COMMANDS.values():
            table.add_row(commands[0], commands[1])
            table.add_section()
        console.print(table)
        print('Після введення команди натисни Enter')

    def line_to_name (self, line):
        line = line.strip().split(' ')
        name = ''
        for each in line:
            name = f'{name}{each[0].capitalize()}{each[1:]} '
        name = name.strip()
        return name

    def do_add_name(self):
        while True:
            line = input("Введіть: <Ім'я>: ")
            if not line:
                print("Будь ласка введіть: <Ім'я>: ")
                continue
            name = self.line_to_name(line)
            if name in self.book:
                print(f"Контакт з ім'ям '{name}' вже існує.")
                return
            try:
                record = NoteRecord(name)
                self.book.add_record(record)
                print(f"Контакт з ім'ям '{name}' успішно створено.")
                break
            except ValueError as e:
                print(f"Помилка при створенні контакту: {e}")

    def do_delete_name(self):
        pass
    def do_add_phone(self, line):
        name = self.line_to_name(line)
        record = self.book.get(name)

        if not record:
            print(f"Контакт з ім'ям '{name}' не знайдено.")
            return
        phone = input ('Введіть номер телефону: 10 цифр:  ')

        try:
            record.add_phone(phone)
            print(f"Телефон '{phone}' додано до контакта '{name}'.")
        except ValueError as e:
            print(f"Помилка при додаванні телефону: {e}")

    def do_delete_phone(self, line):
        pass
    def do_add_birthday(self, line):
        pass
    def do_add_email(self, line):
        name = self.line_to_name(line)
        record = self.book.get(name)
        if not record:
            print(f"Контакт з ім'ям '{name}' не знайдено.")
            return
        email = input('Введіть email:  ')
        try:
            record.add_email(email)
            print(f"Email '{email}' додано до контакта '{name}'.")
        except IndexError as e:
            print(f"Помилка при додаванні email: {e}")

    def do_delete_email(self, line):
        pass
    def do_add_address(self, line):
        pass
    def do_delete_address(self, line):
        pass
    def do_list_book(self):
        if not self.book.data:
            print("Адресна книга порожня.")
        else:
            table = Table(show_header=True, header_style="bold magenta", border_style='bold violet')
            table.add_column('Name')
            table.add_column("Phone")
            table.add_column("Address")
            table.add_column("Email")
            table.add_column("Birthday")
            for record_id, record in self.book.data.items():
                phones = '; '.join(str(phone) for phone in record.phones)
                birthday_info = record.birthday.value if record.birthday else ""
                address_info = record.address.value if record.address else ""
                email_info = record.email.value if record.email else ""
                table.add_row(record.name.value, phones, address_info, email_info, birthday_info)
                table.add_section()
            console.print(table)

    def do_list_note(self):
        pass
    def do_find_record_by_trem(self, line):
        pass
    def do_find_notes_by_term(self, term):
        pass
    def do_days_to_birthday(self, line, when=9999): # >>>birthday John (до дня народження контакту John, залишилось 354 днів)
        pass
    def do_when (self, days):
        pass
    def do_add_note(self, line):
        pass
    def do_find_note_by_name(self, line):
        pass
    def do_delete_all_notes(self, line):
        pass

    def do_edit_note(self, line):
        pass

    def do_sort_files(self, line):
        pass

class CommandValidator(Validator):
    def validate(self, document):
        text = document.text
        if text.startswith("add_phone"):
            x = text.strip().split(" ")
            if len(x) < 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

        if text.startswith("delete_phone"):
            x = text.strip().split(" ")
            if len(x) < 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

        if text.startswith("add_birthday"):
            x = text.strip().split(" ")
            if len(x) < 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

        if text.startswith("find_record_by_trem"):
            x = text.split(" ")
            if len(x) == 1:
                raise ValidationError(message="Введіть: будь який термін для пошуку", cursor_position=len(text))

controller = Controller()

def handle_command(command):
    if command.lower().startswith("add_name"):
        return controller.do_add_name()
    elif command.lower().startswith("delete_name"):
        return controller.do_delete_name()
    elif command.lower().startswith("help"):
        return controller.do_help()
    elif command.lower().startswith("add_phone"):
        first_space_index = command.find(' ')
        _, name = [command[:first_space_index], command[first_space_index+1:]]
        return controller.do_add_phone(name)
    elif command.lower().startswith("delete_phone"):
        first_space_index = command.find(' ')
        _, name = [command[:first_space_index], command[first_space_index+1:]]
        return controller.do_delete_phone(name)
   
def main():
    controller.do_load()
    print("Ласкаво просимо до Адресної Книги")
    controller.do_when('0')

    while True:
        commands_for_interp = {}
        for command in COMMANDS.keys():
            commands_for_interp[command] = None
        command_interpreter = NestedCompleter.from_nested_dict(commands_for_interp)

        user_input = prompt('Enter command: ', completer=command_interpreter, validator=CommandValidator(),
                            validate_while_typing=False)
        if user_input.lower() == "exit":
            controller.do_save()
            print("Good bye!")
            break
        response = handle_command(user_input)

if __name__ == "__main__":
    main()
