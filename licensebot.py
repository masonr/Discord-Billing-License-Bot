# licensebot.py
# Author: Mason Rowe <mason@rowe.sh>
# Project: Host Billing License Verification Discord Bot
# License: WTFPL <http://www.wtfpl.net/>
# Last Updated: 05 Aug 2023
#
# Purpose: A simple Discord bot that will verify WHMCS and Blesta Billing Panel licenses
#          to ensure hosts are not using nulled/cracked billing panels
#
# Tested Python version: v3.11.2

import discord
import requests
import datetime
from bs4 import BeautifulSoup

# Host Billing License Verification Discord Bot Token
# !!! KEEP TOKEN PRIVATE OR BOT MAY BE COMPROMISED !!!
TOKEN = 'REDACTED_REPLACE-WITH-YOUR-TOKEN'
WHMCS_USER = 'REDACTED_REPLACE-WITH-YOUR-USERNAME' # WHMCS.com account email
WHMCS_PASS = 'REDACTED_REPLACE-WITH-YOUR-PASSWORD' # WHMCS.com account password (some special characters might have issues)
WHMCS_COOKIE = '' # (leave blank) WHMCS session cookie
WHMCS_COOKIE_MODIFIED = datetime.datetime.utcnow() # WHMCS session cookie last updated time
# Initialize Discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# check_domain()
#   Purpose: Checks the provided domain against the specified panel to determine the validity of the
#            license for that domain.
#   Params:
#     - domain: the billing domain of the host
#     - panel: the type of billing panel license to validate against
#   Returns: The result of the license check ('Valid', 'Invalid', or 'Error')
def check_domain(domain, panel):
    # declare use of global variables (or else local copies will be made)
    global WHMCS_USER, WHMCS_PASS, WHMCS_COOKIE, WHMCS_COOKIE_MODIFIED

    # WHMCS License Check
    if (panel == 'whmcs'):
        url = 'https://www.whmcs.com/members/verifydomain.php'
        data = { 'domain': domain }
        # get WHMCS session token
        sesh_token = get_whmcs_cookie()
        if (sesh_token == 'Error'):
            return 'Error'
        cookies = { 'WHMCSXbAkzYLZLCZ4': sesh_token }
    # Blesta License Check
    elif (panel == 'blesta'):
        url = 'https://account.blesta.com/client/plugin/license_verify/'
        # need to grab the csrftoken and sid to submit a valid Blesta query
        try:
            s = requests.get('https://account.blesta.com/client/plugin/license_verify/')
        except requests.exceptions.RequestException as e:
            # error encountered - print error in console and return error status
            print(e)
            return 'Error'
        # parse the html of Blesta's license verification webpage
        soup = BeautifulSoup(s.text, 'html.parser')
        # extract csrftoken from response
        csrftoken = soup.find('input', dict(name='_csrf_token'))['value']
        data = { 'search': domain, '_csrf_token': csrftoken }
        # extract sid from response's cookies
        sid = s.cookies['blesta_sid']
        cookies = { 'blesta_sid': sid } # add sid to cookies
    # Unknown License Check
    else:
        return 'Error'

    # HTTP POST message has been staged, now send POST to the corresponding license verification page
    try:
        r = requests.post(url = url, data = data, cookies = cookies, timeout=10)
    except requests.exceptions.RequestException as e:
        # error encountered - print error in console and return error status
        print(e)
        return 'Error'
    success = 'This domain is authorized to be using' # valid licenses will contain this text in the response
    failed = 'This domain is not authorized to be using' # invalid licenses will contain this text in the response
    if (success in r.text):
        # Valid license
        return 'Valid'
    elif (failed in r.text):
        # Invalid license
        return 'Invalid'
    else:
        # Error (neither success nor failed text found in POST response)
        return 'Error'

# get_whmcs_cookie()
#   Purpose: Get WHMCS session cookie to bypass reCAPTCHA requirement on forms. Updates cookie if it is out of date.
#   Params: (none)
#   Returns: A string containing the WHMCS cookie value for the current active session
def get_whmcs_cookie():
    # declare use of global variables (or else local copies will be made)
    global WHMCS_USER, WHMCS_PASS, WHMCS_COOKIE, WHMCS_COOKIE_MODIFIED

    # check if cookie is unset (initial startup) or is expired (30+ mins old)
    if (WHMCS_COOKIE == '' or datetime.datetime.utcnow() > (WHMCS_COOKIE_MODIFIED + datetime.timedelta(minutes=30))):
        # WHMCS cookie needs updating
        # need to get new WHMCS session, but first we need a temporary cookie
        url = 'https://www.whmcs.com/members/clientarea.php'
        try:
            s = requests.get(url)
        except requests.exceptions.RequestException as e:
            # error encountered - print error in console and return error status
            print(e)
            return 'Error'
        # extract temp WHMCS cookie value from response's cookies
        c_val = s.cookies['WHMCSXbAkzYLZLCZ4']
        cookies = { 'WHMCSXbAkzYLZLCZ4': c_val } # add WHMCS cookie value to cookies
        # prepare WHMCS username and password for login
        data = { 'username': WHMCS_USER, 'password': WHMCS_PASS }
        # create new http session
        sesh = requests.Session()
        # change url to WHMCS login page (no reCAPTCHA requirement)
        url = 'https://www.whmcs.com/members/dologin.php'
        # HTTP POST message has been staged, now send POST to the WHMCS login page
        try:
            sesh.post(url = url, data = data, cookies = cookies, timeout=10)
            # extract new WHMCS session cookie
            WHMCS_COOKIE = sesh.cookies['WHMCSXbAkzYLZLCZ4']
            # update last session cookie modified time
            WHMCS_COOKIE_MODIFIED = datetime.datetime.utcnow()
        except requests.exceptions.RequestException as e:
            # error encountered - print error in console and return error status
            print(e)
            return 'Error'
    # we either have a non-expired session or retrieved a new session cookie, return it
    return WHMCS_COOKIE

# create_embed()
#   Purpose: Create the Discord embed object that will be displayed with the license check results
#   Params:
#     - domain: the billing domain of the host
#     - result: the result from checking validity of billing license
#     - license_type: the type of billing panel license checked
#   Returns: An embed object to place in the Discord response
def create_embed(domain, result, license_type):
    # add title to response
    embed = discord.Embed(title = "License Verification Summary for " + domain)
    embed.add_field(name='Domain', value=domain, inline=False) # display entered domain
    # license is valid
    if (result == 'Valid'):
        embed.add_field(name='Status', value='Verified', inline=False)
        embed.set_thumbnail(url = "https://files.rowe.sh/license-bot/images/valid.png")
    # license is invalid
    elif (result == 'Invalid'):
        embed.add_field(name='Status', value='Invalid', inline=False)
        embed.set_thumbnail(url = "https://files.rowe.sh/license-bot/images/invalid.png")
    # error has occured
    else:
        embed.description = "An error has occurred. Please note that the domain given as an argument must not include the preceding scheme (http:// or https://) nor a subdomain of 'www.' (i.e. to check the license status of http://www.host.net, run `!license host.net`)"
        embed.add_field(name='Status', value='Error', inline=False)
        embed.set_thumbnail(url = "https://files.rowe.sh/license-bot/images/error.png")
    # add license type checked
    embed.add_field(name='License', value=license_type, inline=False)
    # create footer message with timestamp
    now = datetime.datetime.utcnow()
    time = now.strftime('%Y-%m-%d %H:%M')
    embed.set_footer(text="Verified by " + client.user.name + " at " + time + " UTC")
    return embed # return Discord embed object

# on_message()
#   Purpose: Catches any entered comments in the Discord server/channel/private chat and
#            completes a license check if a bot command was entered
#   Params:
#     - message: the raw message a person entered in Discord chat
#   Returns: (none)
@client.event
async def on_message(message):
    # ignore messages from self
    if message.author == client.user:
        return

    message_split = message.content.split() # split message into space delimited pieces
    domain = return_msg = "" # initialize domain variable

    # handles if bot is mentioned
    if client.user.mentioned_in(message) and message.mention_everyone is False:
        return_msg = "Hello! I can check domains for valid WHMCS or Blesta licenses, enter `!license help` for usage."
        await message.channel.send(return_msg)
        return

    # handles insufficient number of arguments and help command
    if message.content.startswith(('!license', '!licence', '!whmcs', '!blesta')):
        if (len(message_split) != 2):
            # invalid number of arguments, print error message
            return_msg = "Invalid number of arguments, enter `!license help` for usage."
        if (message_split[1] == 'help'):
            # print help/usage summary
            return_msg = "Host Billing License Verification Bot v0.1\nhttps://github.com/masonr/discord-billing-license-bot/"
            return_msg += "\n\nUsage:\n\t!command [domain]\n\t!command help\n\nCommands:\n"
            return_msg += "\t`!license` - checks WHMCS and Blesta license validity\n"
            return_msg += "\t`!licence` - (same as above)\n"
            return_msg += "\t`!whmcs` - checks WHMCS license validity\n"
            return_msg += "\t`!blesta` - checks Blesta license validity\n\nCreated by Mason Rowe (https://rowe.sh)"
        if (return_msg != ""):
            # if return message is set, return the error/help message and exit
            await message.channel.send(return_msg)
            return
        # extract domain from message and santize common mistakes
        domain = message_split[1].replace('http://','').replace('https://','')
        if (domain[:4] == 'www.'):
            domain = domain[4:]
        if ('/' in domain):
            domain = domain.split('/')[0]
        
    else:
        # terminate early if message is not a bot command
        return

    # handles "!license" or "!licence" (thanks Brits!) chat command
    # checks both WHMCS and Blesta licenses for validity
    if message.content.startswith(('!license', '!licence')):
        whmcs_result = check_domain(domain, 'whmcs')
        if (whmcs_result == 'Valid'):
            # WHMCS license is valid, create Valid WHMCS embed object
            embed = create_embed(domain, whmcs_result, "WHMCS")
        else:
            blesta_result = check_domain(domain, 'blesta')
            if (blesta_result == 'Valid'):
                # Blesta license is valid, create Valid Blesta embed object
                embed = create_embed(domain, blesta_result, "Blesta")
            else:
                # license is either invalid or resulted in error
                embed = create_embed(domain, whmcs_result, "WHMCS / Blesta")
        # reply in Discord chat with results
        await message.channel.send(embed=embed)
    # handles "!whmcs" chat command
    # checks only WHMCS license for validity
    elif message.content.startswith('!whmcs'):
        whmcs_result = check_domain(domain, 'whmcs')
        embed = create_embed(domain, whmcs_result, "WHMCS")
        # reply in Discord chat with results
        await message.channel.send(embed=embed)
    # handles "!blesta" chat command
    # checks only Blesta license for validity
    elif message.content.startswith('!blesta'):
        blesta_result = check_domain(domain, 'blesta')
        embed = create_embed(domain, blesta_result, "Blesta")
        # reply in Discord chat with results
        await message.channel.send(embed=embed)

# on_ready()
#   Purpose: Runs after Discord bot has connected to the server
#   Params: (none)
#   Returns: (none)
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

# run the Discord bot
client.run(TOKEN)
