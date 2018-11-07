# licensebot.py
# Author: Mason Rowe <mason@rowe.sh>
# Project: Host Billing License Verification Discord Bot
# License: WTFPL <http://www.wtfpl.net/>
# Last Updated: 07 Nov 2018
#
# Purpose: A simple Discord bot that will verify WHMCS and Blesta Billing Panel licenses
#          to ensure hosts are not using nulled/cracked billing panels
#
# Tested Python version: v3.6.6

import discord
import requests
import datetime
from bs4 import BeautifulSoup

# Host Billing License Verification Discord Bot Token
# !!! KEEP TOKEN PRIVATE OR BOT MAY BE COMPROMISED !!!
TOKEN = 'REDACTED_REPLACE-WITH-YOUR-TOKEN'
# Initialize Discord client
client = discord.Client()

# check_domain()
#   Purpose: Add a worker to the active workers array
#   Params:
#     - domain: the billing domain of the host
#     - panel: the type of billing panel license to validate against
#   Returns: The result of the license check ('Valid', 'Invalid', or 'Error')
def check_domain(domain, panel):
    # WHMCS License Check
    if (panel == 'whmcs'):
        url = 'https://www.whmcs.com/members/verifydomain.php'
        data = { 'domain': domain }
        cookies = {} # no cookies required for WHMCS lookups
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
        sid = s.cookies['sid']
        cookies = { 'sid': sid } # add sid to cookies
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
        await client.send_message(message.channel, return_msg)
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
            await client.send_message(message.channel, return_msg)
            return
        # extract domain from message
        domain = message_split[1]
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
        await client.send_message(message.channel, embed=embed)
    # handles "!whmcs" chat command
    # checks only WHMCS license for validity
    elif message.content.startswith('!whmcs'):
        whmcs_result = check_domain(domain, 'whmcs')
        embed = create_embed(domain, whmcs_result, "WHMCS")
        # reply in Discord chat with results
        await client.send_message(message.channel, embed=embed)
    # handles "!blesta" chat command
    # checks only Blesta license for validity
    elif message.content.startswith('!blesta'):
        blesta_result = check_domain(domain, 'blesta')
        embed = create_embed(domain, blesta_result, "Blesta")
        # reply in Discord chat with results
        await client.send_message(message.channel, embed=embed)

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
