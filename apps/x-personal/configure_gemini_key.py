"""Store a Gemini API key in the current Windows user's Credential Manager."""
from getpass import getpass

from x_personal.credentials import store_gemini_api_key


def main():
    api_key = getpass('Enter a NEW Gemini API key (input is hidden): ')
    store_gemini_api_key(api_key)
    print('Gemini API key stored securely for the current Windows user.')


if __name__ == '__main__':
    main()
