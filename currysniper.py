import asyncio
import json
import configparser
import re
import sys
# import pytesseract
# import cv2
import time
import pyrogram
import math
from collections import Counter
from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler
from pyrogram.errors import FloodWait
from hdwallet import BIP44HDWallet
from hdwallet.cryptocurrencies import EthereumMainnet
from hdwallet.derivations import BIP44Derivation
from hdwallet.utils import generate_mnemonic
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.exceptions import TimeExhausted
from typing import Optional


class CurrySniper:

    def __init__(self, userID, currybot, _network=1):
        """

        :param userID: int, unique identifier of the licensed user
        :param handlerGUI: CurrySniperBot message handler, granting the licensed user access to all functionality
        :param _network: bool, network to use, defaults to BSC (1), Testnet supported (0)
        """

        # CurrySniper version
        self.version = 'beta v0.4'

        # User ID and their handler with the CurrySniperBot
        self.userID = userID
        self.currybot = currybot
        self.handlerGUI = self.currybot.add_handler(MessageHandler(self.telegramGUI, filters=filters.chat(self.userID)))

        # Read the sneedphrase from the txt file, or generate one if none exists prior
        try:
            with open('doc/sneed.txt', 'r') as f:
                self.sneed = f.read()
        except FileNotFoundError:
            # No sneed exists
            self.sneed: str = generate_mnemonic(language="english", strength=128)
            with open('doc/sneed.txt', 'x') as f:
                f.write(self.sneed)

        # Initialize Ethereum mainnet BIP44HDWallet
        bip44_hdwallet: BIP44HDWallet = BIP44HDWallet(cryptocurrency=EthereumMainnet)
        # Get Ethereum BIP44HDWallet from mnemonic
        bip44_hdwallet.from_mnemonic(mnemonic=self.sneed, language="english")
        # Clean default BIP44 derivation indexes/paths
        bip44_hdwallet.clean_derivation()

        # Initialize addies and pkeys
        self.addies = []
        self.pkeys = []

        # Get Ethereum BIP44HDWallet information's from address index
        for address_index in range(10):
            # Derivation from Ethereum BIP44 derivation path
            bip44_derivation: BIP44Derivation = BIP44Derivation(
                cryptocurrency=EthereumMainnet, account=0, change=False, address=address_index
            )
            # Drive Ethereum BIP44HDWallet
            bip44_hdwallet.from_path(path=bip44_derivation)
            # Add address and private_key
            self.addies.append(bip44_hdwallet.address())
            self.pkeys.append(bip44_hdwallet.private_key())
            # Clean derivation indexes/paths
            bip44_hdwallet.clean_derivation()

        # Main address of the sniper
        self.main_addy = self.addies[0]

        # User's personal wallet to redeem BNB back, undefined at first
        self.personal_wallet = None

        # Token standard ABI, swap ABI
        self.tokenABI = '[{"constant": false, "inputs": [{"name": "_spender","type": "address"},{"name": "_value","type": "uint256"}],"name": "approve","outputs": [{"name": "","type": "bool"}],"payable": false,"stateMutability": "nonpayable","type": "function"}, {"constant": true,"inputs": [{"name": "_owner","type": "address"}],"name": "balanceOf","outputs": [{"name": "balance","type": "uint256"}],"payable": false,"stateMutability": "view","type": "function"},{"constant": true,"inputs": [],"name": "decimals","outputs": [{"name": "","type": "uint8"}],"payable": false,"stateMutability": "view","type": "function"}]'
        self.swapABI = '[{"inputs":[{"internalType":"address","name":"_factory","type":"address"},{"internalType":"address","name":"_WETH","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountTokenDesired","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountIn","outputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountOut","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsIn","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"reserveA","type":"uint256"},{"internalType":"uint256","name":"reserveB","type":"uint256"}],"name":"quote","outputs":[{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETHSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermit","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermitSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityWithPermit","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapETHForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETHSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]'

        # Swap routers that are supported
        self.routers = {
            'pancakev2': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
            'apeswap': '0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7',
            'pancakev2.Testnet': '0x9Ac64Cc6e4415144C455BD8E4837Fea55603e5c3'
        }

        # Web3 provider: network and swap router
        if _network == 0:
            # Use testnet BNB and testnet pancakev2 router
            self.web3 = Web3(Web3.HTTPProvider('https://data-seed-prebsc-1-s1.binance.org:8545'))
            self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            self.pairing = self.web3.toChecksumAddress("0xae13d989daC2f0dEbFf460aC112a837C89BAa7cd")
            self.router = self.routers['pancakev2.Testnet']

        else:
            # Mainnet, use pancakev2 router by default
            # TODO: look for a better provider
            self.web3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))
            self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            self.pairing = self.web3.toChecksumAddress("0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c")
            self.router = self.routers['pancakev2']

        self.supported_pairings = {
            'busd': self.web3.toChecksumAddress('0xe9e7cea3dedca5984780bafc599bd69add087d56'),
            'usdt': self.web3.toChecksumAddress('0x55d398326f99059ff775485246999027b3197955')
        }

        # TODO: set up routers on the snipe order itself

        # Gas multiplier, to increase during periods of high network congestion
        self.gas_multiplier = 1

        # Balance from the main wallet that is being allocated for snipes, starts out as zero, is increased when
        # placing snipes, decreased by the same amount when completing/cancelling snipes
        self.allocated_main_balance = 0

        # Blacklisted telegram accounts
        self.blacklisted_accounts = ['MissRose_bot', 'shieldy_bot', 'BanhammerMarie2_bot', 'combot', 'GroupHelpBot']

        # Dictionary of active snipes, each new entry has the groupID as key, and another dictionary as values
        self.active_snipes = {}

        try:
            # Look for a previously existing session and start it (for future code maintenance and updates, restart)
            self.user_app = Client('doc/{}'.format(self.userID), config_file='doc/{}.ini'.format(self.userID))
            self.user_app.start()
            msg = 'The program was restarted and your API client was successfully connected. Type /help for a list ' \
                  'of commands.'
            self.currybot.send_message(self.userID, msg)

            # Generating and sending about pasta
            msg = 'CurrySniper running on **{}**\n'.format(self.version)
            msg += 'Part of @DrCurry and the Curry Tool Suite (SPICEMIX). Building new tools for the blockchain to keep up '
            msg += 'with the ever-changing shitcoin scene.'
            self.currybot.send_message(self.userID, msg, parse_mode='markdown')
        except:
            # No existing session, so most likely no previous interaction with the bot. User can /start to define
            # his session
            self.user_app = None

    async def telegramGUI(self, client, message):
        """Connects each of the commands to their respective function"""

        # Command ordered
        split_msg = message.text.split(' ')
        command = split_msg[0][1:].lower()
        # List of parameters and their values, if none are given will return ['']
        parameters = [i.strip() for i in ' '.join(split_msg[1:]).split(';')]

        # For restarting
        if command == 'restart':
            await self.currybot.send_message(self.userID, 'Please, wait a couple seconds while the program restarts.')
            # Need a PM2 handler for the program to restart right after exiting
            sys.exit()

        try:
            # Switch case implementation for every command
            if command == 'sell':
                # Special case, as on this one it needs to be replying to a different message
                await self.sell(parameters, message)
            else:
                # Rest of commands are treated the same way
                await {
                    'start': lambda params: self.start(params),
                    'balance': lambda params: self.balance(params),
                    'resetbalance': lambda params: self.reset_balance(params),
                    'personalwallet': lambda params: self.set_personal_wallet(params),
                    'redeem': lambda params: self.redeem(params),
                    'sneed': lambda params: self.get_sneed(params),
                    'getgroupid': lambda params: self.get_group_ID(params),
                    'snipe': lambda params: self.set_up_snipe(params),
                    'safesnipe': lambda params: self.set_up_snipe(params, safe=True),
                    'activesnipes': lambda params: self.get_active_snipes(params),
                    'cancelsnipe': lambda params: self.cancel_snipe(params),
                    'gasmultiplier': lambda params: self.change_gas_multiplier(params),
                    'snipehelp': lambda params: self.snipe_help(params),
                    'safesnipehelp': lambda params: self.safesnipe_help(params),
                    'help': lambda params: self.help(params),
                    'disclaimer': lambda params: self.disclaimer(params),
                    'about': lambda params: self.about(params)
                }[command](parameters)
        except:
            # Command not supported
            await self.currybot.send_message(self.userID,
                                             'Invalid command! Type /help to see a list of available commands.')

    async def start(self, params):
        """User's CurrySniper set up. Creates a new TG session for the user, guiding them through the process"""

        # Temporarily disconnect the GUI session while the user sets up their accounts
        self.currybot.remove_handler(*self.handlerGUI)

        # First set up message explaining what the CurrySniper does
        msg = 'You are now the proud owner of a CurrySniper license. Before setting anything up, let\'s give you a '
        msg += 'quick rundown of the tool\'s capabilities\n\n'
        msg += 'The CurrySniper, part of DrCurry and the Curry Tool Suite (SPICEMIX), is a sniper that is specifically designed '
        msg += 'to target the so-called fair launches, where the CA gets posted __after__ launch to give everyone a '
        msg += '"fair chance" at buying in. What this sniper essentially does is scrape the telegram group message '
        msg += 'feed, looking for a CA to immediately buy into, ensuring that you truly get in __first__.\n\n'
        msg += 'Of course, there is a big risk related to buying contracts without running them through a rugscreener '
        msg += 'first. It is expected that the user __knows__ how to properly discern between fraudulent and '
        msg += 'legitimate launches. Although it is not always easy, the wins should far outweigh the losses, provided '
        msg += 'you stay away from jeetery.\n\n'
        msg += 'To my knowledge, these kinds of snipers are yet to reach wide adoption. Most of the shitcoin market is '
        msg += 'unaware of the existence of these tools. It is therefore in the user\'s best interest to keep these '
        msg += 'working principles a trade secret, so that the meta around shitcoin launches does not evolve against '
        msg += 'them. Your success sniping greatly depends on your ability to remain quiet about the tool\'s '
        msg += 'functioning, and to not share the tokens you snipe.'

        await self.currybot.send_message(self.userID, msg, parse_mode='markdown')
        # Give the user some time to read through it all
        # await asyncio.sleep(20)

        msg = 'For the sniper to work, you need to provide an API session linked to a telegram account under your '
        msg += 'control, as you will be the one joining groups to __snipe__. Ideally, you should provide an alt '
        msg += 'account API, as you need to provide the phone number and you are essentially giving me full control of '
        msg += 'said account, but that is your call. The account API you set up does **not** necessarily have to be '
        msg += 'the one you are using to interact and set up snipes with the CurrySniperBot, but it will be the '
        msg += 'one you use to join the telegram groups you wish to snipe.\n\nIf you would like to change any of those '
        msg += 'accounts, please contact @CurryDev. Do not worry if this sounds too complicated, our intern, Rakesh, '
        msg += 'will guide you through the whole process.'

        await self.currybot.send_message(self.userID, msg, parse_mode='markdown')
        # Give the user some time to read through it all
        # await asyncio.sleep(15)


        if self.user_app is None:
            # There is no previous existing session

            # Values that will get filled
            api_id = None
            api_hash = None
            phone_number = None
            phone_hash = None

            msg = 'Good day, sir, my name is Rakesh and I will be guiding you through the whole API set up process. '
            msg += 'First I need you to visit [this link](https://my.telegram.org/auth?to=apps), and log in with the '
            msg += 'telegram account you wish to use. When you are done, type /done.'
            await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

            # Handler function
            async def setup(client, message):
                nonlocal api_id, api_hash, phone_number, phone_hash

                code = False  # No verification code has been given
                cmd = message.command[0]

                if cmd == 'done':
                    # Informing user on what to provide
                    msg = 'Great work sir! Now kindly provide your __App api_id__ and __App api_hash__ (which can be '
                    msg += 'found in that webpage) and your phone number (with country code) in separate commands in '
                    msg += 'this manner:\n\n'
                    msg += '/api_id 12345\n/api_hash 0123456789abcdef0123456789abcdef\n/phone_number +34 660 253 957'
                    await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

                elif cmd == 'api_id':
                    # Adding the api_id
                    api_id = message.command[1]
                    msg = 'Registered values:\nAPI ID: `{}`\nAPI hash: `{}`\nPhone number: `{}`'.format(
                        api_id, api_hash, phone_number
                    )
                    await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

                elif cmd == 'api_hash':
                    # Adding the api_hash
                    api_hash = message.command[1]
                    msg = 'Registered values:\nAPI ID: `{}`\nAPI hash: `{}`\nPhone number: `{}`'.format(
                        api_id, api_hash, phone_number
                    )
                    await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

                elif cmd == 'phone_number':
                    # Adding the phone_number
                    phone_number = ' '.join(message.command[1:])
                    msg = 'Registered values:\nAPI ID: `{}`\nAPI hash: `{}`\nPhone number: `{}`'.format(
                        api_id, api_hash, phone_number
                    )
                    await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

                elif cmd == 'code':
                    # Adding the confirmation code
                    code = ''.join(message.command[1].split('-'))

                    try:
                        await self.user_app.sign_in(phone_number, phone_hash, code)
                    except:
                        msg = 'Something went wrong! Let\'s try again.'
                        await self.currybot.send_message(self.userID, msg)
                        code = False
                    else:
                        write_config = configparser.ConfigParser()

                        write_config.add_section('pyrogram')
                        write_config.set('pyrogram', 'api_id', api_id)
                        write_config.set('pyrogram', 'api_hash', api_id)

                        with open('doc/{}.ini'.format(self.userID), 'w') as cfgfile:
                            write_config.write(cfgfile)

                        # Add the user app
                        self.user_app = Client('doc/{}'.format(self.userID),
                                               config_file='doc/{}.ini'.format(self.userID))
                        await self.user_app.start()

                        self.currybot.remove_handler(*setup_handler)
                        # Reestablish the GUI session after their account has been set up
                        self.handlerGUI = self.currybot.add_handler(MessageHandler(self.telegramGUI,
                                                                                   filters=filters.chat(self.userID)))

                        msg = 'You are now successfully logged in! Please, wait a couple seconds while the program ' \
                              'restarts.'
                        await self.currybot.send_message(self.userID, msg)
                        sys.exit()

                if api_id is not None and api_hash is not None and phone_number is not None and code is False:

                    go_ahead_1 = False
                    go_ahead_2 = False

                    # All three values have been inputted, exit the handler
                    try:
                        self.user_app = Client(str(self.userID), api_id, api_hash, workdir='doc')
                        await self.user_app.connect()
                    except:
                        msg = 'Something went wrong! The API values you provided are invalid. Kindly set them up again.'
                        await self.currybot.send_message(self.userID, msg)
                        go_ahead_1 = False
                    else:
                        go_ahead_1 = True

                    try:
                        sent_code = await self.user_app.send_code(phone_number)
                        phone_hash = sent_code.phone_code_hash
                    except FloodWait:
                        msg = 'You requested too many login codes! You will have to try again later, there is nothing '
                        msg += 'the CurrySniperBot can do about that.'
                        await self.currybot.send_message(self.userID, msg)
                        go_ahead_2 = False
                    except:
                        msg = 'Something went wrong! The phone number you provided is invalid. Kindly set it up again.'
                        await self.currybot.send_message(self.userID, msg)
                        go_ahead_2 = False
                    else:
                        go_ahead_2 = True

                    if go_ahead_1 and go_ahead_2:
                        msg = 'Kindly provide the telegram verification code that was just sent to you in this manner:'
                        msg += '\n\n/code 1-2-3-4-5-6\n\n'
                        msg += 'Make sure you separate the verification code digits by hyphens (-), as Telegram '
                        msg += 'immediately expires the verification codes you share across chats.'
                        await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

            # Handler to manage the user set up
            setup_handler = self.currybot.add_handler(MessageHandler(setup,
                                                                     filters=filters.chat(self.userID) &
                                                                             filters.command(
                                                                                 ['done', 'api_id', 'api_hash',
                                                                                  'phone_number', 'code']
                                                                             )))

        else:
            # Reestablish the GUI session after their account has been set up
            self.handlerGUI = self.currybot.add_handler(MessageHandler(self.telegramGUI,
                                                                       filters=filters.chat(self.userID)))

            # A previously existing session exists, no need to do anything else by the user
            msg = 'A telegram account session linked to your license was found. Your license is already set up, there '
            msg += 'is no need for you to provide any more information. You may type /help for a list of commands.\n\n'
            msg += 'If you would like to change the telegram account your session is linked to, please contact me ' \
                   '@CurryDev'
            await self.currybot.send_message(self.userID, msg)

    async def _get_BNB_balance(self, addy):
        """Returns the BNB balance of the requested address

        :param addy: the wallet address of interest

        :return: balance in BNB
        """

        return self.web3.eth.get_balance(addy) * 10 ** -18

    async def _get_token_balance(self, token_contract, addy):
        """Returns an address token balance

        :param token_ontract: the contract address of the token, must be in Checksum mode
        :param addy: the wallet address of interest

        :return: balance of tokens
        """
        tokenContractABI = self.web3.eth.contract(token_contract, abi=self.tokenABI)
        return tokenContractABI.functions.balanceOf(addy).call()

    async def balance(self, params):
        """Sends the user information back about their account balance"""

        # Get balances
        balances = []
        main_balance = await self._get_BNB_balance(self.addies[0])
        balances.append(main_balance)
        msg = 'Wallet breakdown:\n'
        msg += 'Main wallet: {:.5f} BNB\n'.format(main_balance)
        for i in range(9):
            balance = await self._get_BNB_balance(self.addies[i+1])
            balances.append(balance)
            msg += 'Wallet {}: {:.5f} BNB\n'.format(i + 2, balance)

        msg = 'Total account balance: **{:.5f} BNB**\n\n'.format(sum(balances)) + msg

        # Ask for more funds
        msg += '\nYou may add more funds to your account by sending them to your main wallet:\n' \
               '`{}`'.format(self.main_addy)

        await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

    async def _send_proxy_balances(self, amounts):
        """Sends the defined amounts of BNB from the main wallet to the proxy wallets

        Used when setting up a snipe, to have in each of the proxy wallets the necessary amount for the order

        :param amounts: array len 9, amount of BNB to send from the main wallet to each of the proxy wallets
        """

        gas_price = self.web3.eth.gasPrice
        gas_spent = self.gas_multiplier * gas_price * 30000 / 10 ** 18
        nonce = self.web3.eth.get_transaction_count(self.main_addy, 'pending')

        for i in range(len(amounts)):
            signed_tx = self.web3.eth.account.sign_transaction(dict(
                nonce=nonce + i,
                gasPrice=gas_price,
                gas=30000,
                to=self.addies[i + 1],
                value=self.web3.toWei(amounts[i] - gas_spent, 'ether')
            ),
                self.pkeys[0])
            self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

    async def _send_proxy_balances_back(self, amounts):
        """Sends a defined BNB amount from the proxy wallets back to the main wallet

        The gas necessary to pay for this transfer is obtained from the amount that is to be transferred, meaning that
        the actual value received will be slightly less. Gas values are computed at the time of transfer. This function
        does not account for the emergency gas that is to be left on each of the proxy wallets (0.1 BNB), but it will
        not send amounts under that value.

        :param amounts: array, amount of BNB to send back from each of the proxy wallets.
        """

        gas_price = self.web3.eth.gasPrice
        gas_spent = self.gas_multiplier * gas_price * 30000 / 10 ** 18

        for i in range(len(amounts)):
            # Only send the transaction if the amount is greater than 0.01 beans, if not it is not worth it
            if amounts[i] > 0.01:
                signed_tx = self.web3.eth.account.sign_transaction(dict(
                    nonce=self.web3.eth.get_transaction_count(self.addies[i + 1], 'pending'),
                    gasPrice=gas_price,
                    gas=30000,
                    to=self.main_addy,
                    value=self.web3.toWei(amounts[i] - gas_spent, 'ether')
                ),
                    self.pkeys[i + 1])
                self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

    async def reset_balance(self, params):
        """Resets wallet balances, leaving the main wallet with most funds, and the rest with 0.03 BNB for gas

        Method should not be used if there are any active snipes, prompt the user if he tries to."""

        if len(self.active_snipes) != 0:
            msg = 'Balance cannot be reset as there are active snipes going on. Type /activeSnipes to see ' \
                  'a quick rundown of the groups you are sniping.'
            await self.currybot.send_message(self.userID, msg)
        else:
            excess_proxy_balances = [await self._get_BNB_balance(addy) - 0.03 for addy in self.addies[1:]]
            self.allocated_main_balance = 0
            await self._send_proxy_balances_back(excess_proxy_balances)
            await self.currybot.send_message(self.userID, 'Balance is being reset. Please, wait a couple seconds for '
                                                          'the transactions to go through.')

    async def set_personal_wallet(self, params):
        """Sets a user's personal wallet under their control to send funds back to. If no parameters are given, shows
        the user's specified personal wallet"""

        if params[0] != '':
            # An actual wallet gets provided
            try:
                self.personal_wallet = self.web3.toChecksumAddress(params[0])
            except:
                await self.currybot.send_message(self.userID,
                                                 'Something went wrong! the address you provided is invalid.')
            else:
                msg = 'Your personal wallet:\n`{}`\n\nPerforming a /redeem command will send BNB from the main wallet ' \
                      'back to this address.'.format(self.personal_wallet)
                await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

        else:
            # No parameters given, check the actual personal wallet
            if self.personal_wallet is not None:
                msg = 'Your personal wallet:\n`{}`\n\nPerforming a /redeem command will send BNB from the main wallet ' \
                      'back to this address.'.format(self.personal_wallet)
                await self.currybot.send_message(self.userID, msg, parse_mode='markdown')
            else:
                msg = 'Your personal wallet is not defined. You can do so by using the following command:\n' \
                      '/personalWallet 0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B\n\n' \
                      'Performing a /redeem command will send BNB from the main wallet back to this address.'
                await self.currybot.send_message(self.userID, msg)

    async def redeem(self, params):
        """Redeems an amount of BNB from the main wallet back to the user's personal wallet"""

        if self.personal_wallet is None:
            msg = 'Your personal wallet is not defined. You can do so by using the following command:\n' \
                  '/personalWallet 0x89205A3A3b2A69De6Dbf7f01ED13B2108B2c43e7\n\n' \
                  'Performing a /redeem command will send BNB from the main wallet back to this address.'
            await self.currybot.send_message(self.userID, msg)
        else:
            try:
                redeem_amount = float(params[0])
            except ValueError:
                await self.currybot.send_message(self.userID, 'Invalid amount!')
            else:
                available_balance = await self._get_BNB_balance(self.main_addy)
                if redeem_amount > available_balance - self.allocated_main_balance - 0.03:
                    msg = 'Not enough funds! Village starving. You can check your balance by typing /balance.\n\n' \
                          'Keep in mind that the CurrySniper always leaves a minimum of 0.03 beans on every wallet ' \
                          'that has been used for emergency gas purposes. Funds that are being allocated for active ' \
                          'snipes cannot be redeemed.'
                    await self.currybot.send_message(self.userID, msg)
                else:
                    gas_price = self.web3.eth.gasPrice
                    gas_spent = self.gas_multiplier * gas_price * 30000 / 10 ** 18
                    signed_tx = self.web3.eth.account.sign_transaction(dict(
                        nonce=self.web3.eth.get_transaction_count(self.main_addy, 'pending'),
                        gasPrice=gas_price,
                        gas=30000,
                        to=self.personal_wallet,
                        value=self.web3.toWei(redeem_amount - gas_spent, 'ether')
                    ),
                        self.pkeys[0])
                    tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    msg = 'Transaction is [on its way](https://bscscan.com/tx/{}).'.format(tx_hash.hex())
                    await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

    async def get_sneed(self, params):
        """Sends a message with the user's seed phrase, MetamMask compatibility"""

        await self.currybot.send_message(self.userID,
                                         'This is your sneed phrase:\n`{}`'.format(self.sneed), parse_mode='markdown')

    async def get_group_ID(self, params):
        """Gets the group ID of the chatroom the user next posts a message to"""

        async def _get_ID(client, message):
            group_id = message.chat.id
            self.user_app.remove_handler(*self.ID_handler)
            await self.currybot.send_message(self.userID, 'Group ID: `{}`'.format(group_id), parse_mode='markdown')

        msg = 'Command is running! You will get the ID of the next group you post in, public or private.'
        await self.currybot.send_message(self.userID, msg)
        self.ID_handler = self.user_app.add_handler(MessageHandler(_get_ID, filters=filters.me))

    async def _calculate_profit(self, buytx, selltx):
        """Calculates the profit in a snipe order, defined as the amount of BNB sold minus the total gas spent and
         amount bought

        :param buytx: array, containing hashes of all the buy tx made. Will be None if that transaction failed.
        :param selltx: array, containing hashes of all the sell tx made. Will be None if that transaction failed.
        :return: profit, result of the trade, whether it is a profit or a loss.
        """
        # Firstly, make sure that all the tx went through
        pass

    async def _get_maximum_tx(self, tokenToBuy, tokenContractABI, router_contract, pairing, nWallets):
        """Calculates the maximum amount of tokens that it is possible to dump via iterating

        This represents the maximum amount that the wallets will be able to dump

        :param tokenContractABI: smart contract of the token to sell
        :param router_contract: smart contract of the swap router
        :param nWallets: number of wallets that hold the token
        :return: sell_order, honey: amount of balance to sell to not trigger max tx, 0 if found to be a honeypot
        """

        balances = [tokenContractABI.functions.balanceOf(self.addies[i]).call() for i in range(nWallets)]
        # Select the wallet that holds the most tokens
        index_max = balances.index(max(balances))
        holder = self.addies[index_max]
        # Balances to start iterating with
        balance_to_sell = balances[index_max]
        print('balance to sell: {}'.format(balance_to_sell))
        balance_lower = int(balance_to_sell * 0.03)
        balance_upper = balance_to_sell
        sell_order = int((balance_lower + balance_upper)/2) # Middle point to start iterating

        # Data to not replicate
        gas = self.web3.toWei('5', 'gwei')
        nonce = self.web3.eth.get_transaction_count(holder, 'pending')

        def sendtx(sell):
            pcstx = router_contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                sell, 0,
                [tokenToBuy, pairing],
                holder,
                (int(time.time()) + 1000000)
            ).buildTransaction({
                'from': holder,
                'gasPrice': gas,
                'nonce': nonce
            })

        try:
            try:
                # Dump whole stack
                sendtx(balance_to_sell)
            except:
                # Cant dump whole stack, try to dump the bare minimum
                sendtx(balance_lower)
                # If it fails, raises error that will be catched alerting user that they will have to test manually

                # If it does work, continues to finding the sweet spot, total of 10 iterations
                for i in range(10):
                    try:
                        sendtx(sell_order)
                    except:
                        # End of iteration reached, and cant sell the middle point, return the lower bound
                        if i == 9:
                            sell_order = balance_lower
                            break
                        # Can't sell the middle point, lower it, and repeat
                        balance_upper = sell_order
                        sell_order = int((balance_lower + sell_order) / 2)
                    else:
                        # End of iteration reached, and can sell the middle point, return the lower bound
                        if i == 9:
                            break
                        # It's possible to sell the middle point, raise the lower point to it, and repeat
                        balance_lower = sell_order
                        sell_order = int((balance_lower + balance_upper) / 2)
            else:
                # Was able to dump whole stack
                sell_order = balance_to_sell
                pass
        except:
            # Can't dump the bare minimum, either honeypot or user will have to sell manually
            # Smelled the spice and tasted the curry
            sell_order = 0

        return sell_order

    async def sell(self, parameters, message):
        """Sells the token that the message is replying to"""
        try:
            original_message = message.reply_to_message
        except:
            # Did not reply to any message
            msg = 'Invalid command! You need to reply to a snipe report to sell that token.'
            await self.currybot.send_message(self.userID, msg)
            return
        else:
            # Full text that was sent in markdown - get the contract address from here
            pasta = original_message.text.markdown.split('poocoin')[1]
            print(pasta)
            pattern = '0x[a-fA-F0-9]{40}'
            tokenToSell = self.web3.toChecksumAddress(re.findall(pattern, pasta)[0])

            # Getting moonbag parameter, it can either be predefined or overwritten in the sell command
            if parameters[0] != '':
                # Moonbag parameter overwritten
                try:
                    tosell = int(parameters[0])
                except:
                    msg = 'Invalid command! The amount to sell you provided is invalid. Type /help for more ' \
                          'information.'
                    await self.currybot.send_message(self.userID, msg)
                    return
                else:
                    # See if the amount to sell is a valid percentage
                    if tosell < 0 or tosell > 100:
                        msg = 'Invalid command! The amount to sell you provided is invalid. Type /help for more ' \
                              'information.'
                        await self.currybot.send_message(self.userID, msg)
                        return
                    # All checks passed, moonbag will be the remainder
                    moonbag = 100 - tosell
            else:
                # Moonbag parameter not overwritten, see if it was actually defined
                if 'moonbag' in pasta:
                    moonbag = int(pasta.split('moonbag of ')[1][:-2])
                else:
                    # Not predefined, will try to sell all
                    moonbag = 0
        print('moonbag: {}'.format(moonbag))

        # token contract
        tokenContractABI = self.web3.eth.contract(tokenToSell, abi=self.tokenABI)

        # Getting the wallets that hold the token
        holders = [addy for addy in self.addies if tokenContractABI.functions.balanceOf(addy).call() > 0]

        # No wallets hold the token, alert the user and exit
        if len(holders) == 0:
            msg = 'Unable to sell as none of your wallets hold the token.'
            await self.currybot.send_message(self.userID, msg)
            return

        # Router contract
        # TODO: add support for apeswap
        router_contract = self.web3.eth.contract(address=self.router, abi=self.swapABI)
        transactionRevertTime = 20

        # Getting max transaction
        maxtx = await self._get_maximum_tx(tokenToSell, tokenContractABI, router_contract, self.pairing, 10)
        maxtx = int(maxtx)

        if maxtx == 0:
            # Unable to sell, inform user that they will have to check it manually
            msg = 'Unable to sell as the detected maximum transaction was 0. Please, try selling manually.'
            await self.currybot.send_message(self.userID, msg)
            return

        # Rest of selling parameters
        gasprice = self.gas_multiplier * self.web3.toWei('7', 'gwei')
        selltx = []
        msg = 'Sell order executed for `{}`\n\n'.format(tokenToSell)

        # All previous checks passed, dump each wallet in succession
        for holder in holders:
            # Dumping each wallet, in order
            balance = tokenContractABI.functions.balanceOf(holder).call()
            balance_sell = int(balance * (100 - moonbag) / 100)
            nonce = self.web3.eth.get_transaction_count(holder, 'pending')

            # Adding to pasta
            if holder == self.main_addy:
                msg += 'Main wallet breakdown:\n'
            else:
                holder_number = holders.index() + 1
                msg += 'Wallet {} breakdown:\n'.format(holder_number)

            if balance == 0:
                # Wallet holds none, skip to next wallet, and inform user accordingly
                msg += 'Holds no tokens, unable to sell.\n\n'
                continue

            if balance_sell <= maxtx:
                # Can just dump all the stack at once
                try:
                    # Sell transaction, which might still fail, are made with half the buying gas
                    pcstx = router_contract.functions. \
                        swapExactTokensForETHSupportingFeeOnTransferTokens(
                        balance_sell, 0,
                        [tokenToSell, self.pairing],
                        holder,
                        int(time.time()) + transactionRevertTime
                    ).buildTransaction({
                        'from': holder,
                        'gasPrice': gasprice,
                        'nonce': nonce
                    })
                except Exception as e:
                    # Can't sell, inform the user but continue trying on later ones
                    msg += 'Encountered an error selling: {}\n'.format(e)
                    cant_sell = [True]
                else:
                    # Transaction is at least possible
                    try:
                        signed_txn = self.web3.eth.account.sign_transaction(pcstx, self.pkeys[self.addies.index(holder)])
                        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    except Exception as e:
                        # In case it fails here, same fail message
                        msg += 'Encountered an error selling: {}\n'.format(e)
                        selltx.append(None)
                        cant_sell = [True]
                    else:
                        # Sell transaction got sent, might still fail when mining
                        msg += '[Solded](https://bscscan.com/tx/{}).\n'.format(tx_hash.hex())
                        selltx.append(tx_hash.hex())
                        cant_sell = [False]

            else:
                # Need to dump in waves, a number of times to sell
                n_sells = math.ceil(balance_sell / maxtx)
                cant_sell = [False for i in range(n_sells)]
                for j in range(n_sells):
                    # Dump each of these times
                    if j == n_sells - 1:
                        # Last dump, sell remaining tokens
                        maxtx = int(balance_sell - maxtx * (n_sells - 1))
                    try:
                        # Sell transaction, which might still fail, are made with half the buying gas
                        pcstx = router_contract.functions. \
                            swapExactTokensForETHSupportingFeeOnTransferTokens(
                            maxtx, 0,
                            [tokenToSell, self.pairing],
                            holder,
                            int(time.time()) + transactionRevertTime
                        ).buildTransaction({
                            'from': holder,
                            'gasPrice': gasprice,
                            'nonce': nonce + j
                        })
                    except Exception as e:
                        # Can't sell, inform the user but continue trying on later ones
                        msg += 'Encountered error on sell #{}: {}\n'.format(j + 1, e)
                        cant_sell[j] = True
                    else:
                        # Transaction is at least possible
                        try:
                            signed_txn = self.web3.eth.account.sign_transaction(pcstx, self.pkeys[self.addies.index(holder)])
                            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                        except Exception as e:
                            # In case it fails here, same fail message
                            msg += 'Encountered error on sell #{}: {}\n'.format(j + 1, e)
                            selltx.append(None)
                            cant_sell[j] = True
                        else:
                            # Sell transaction got sent, might still fail when mining
                            msg += '[Solded #{}](https://bscscan.com/tx/{}).\n'.format(j + 1, tx_hash.hex())
                            selltx.append(tx_hash.hex())

            if all(cant_sell):
                # Could not sell a single one, inform the user
                msg += 'The program was not able to sell any of the tokens. You should check it manually.'
                await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

            if any(cant_sell):
                # Could not sell some
                msg += 'The program was not able to sell some tokens'
                await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

        if moonbag != 0:
            if len(holders) > 1:
                wallets = ' {} wallets'.format(len(holders))
            else:
                wallets = ' the main wallet'
            msg += '\nLeft a {}% moonbag on'.format(moonbag) + wallets

        # Send the message
        await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

        # Add final message of estimated profit
        # msg = 'Autosell report for `{}` {}:\n'.format(snipe_chat_ID, name)
        # profit = await self._calculate_profit(buytx, selltx)
        # msg += 'Estimated profit: **{:.5f} BNB**'.format(profit)
        # await self.currybot.send_message(self.userID, msg, parse_mode='markdown')



    async def _snipe(self, snipe_chat_ID, snipe_parameters, safesnipe=False):
        """Sets up the telegram message handler and executes the snipe order

        The telegram message handler scrapes all messages and looks for a contract address. If one is found, it will
        immediately buy it following the defined parameters

        :param snipe_chat_ID: unique chat ID of the group that is to be sniped
        :param snipe_parameters: dictionary, parameters that set up the snipe
        :param safesnipe: bool, whether to perform a quick honeypot check before, defaults to False
        """

        transactionRevertTime = snipe_parameters['reverttime']
        # What is the LP pairing with
        pairing = snipe_parameters['pairing']

        # Safesnipe option
        if safesnipe is True:
            honeypot_default = snipe_parameters['honeydefault']

        # Regex pattern
        pattern = '0x[a-fA-F0-9]{40}'

        # TODO: restructure this
        # Wallet to send the funds to, this is set with the nWallets argument in the snipe command line
        nApes = len(snipe_parameters['amounts'])
        nWallets = snipe_parameters['holdwallets']
        sendTo = ['' for i in range(nApes)]
        # Structure receiving wallets
        reTX = int(nApes / nWallets)  # number of receiver TX
        for i in range(nApes):
            if i == nApes - 1:
                sendTo[i] = self.addies[nWallets - 1]
            else:
                sendTo[i] = self.addies[int(i / reTX)]
            # End result is an array that distributes the TX between the receiving wallets equally, while the remainder
            # are directed to the last wallet, to try and avoide max wallet shenanigans

        amounts = []
        if pairing == self.pairing:
            # BNB pairing, convert to wei each value:
            for i in range(nApes):
                amounts.append(self.web3.toWei(float(snipe_parameters['amounts'][i]), 'ether'))
        else:
            # Pairing is a different one
            for i in range(nApes):
                amounts.append(snipe_parameters['amounts'][i] * 10**12)

        # Tx hashes to show the user afterwards
        buytx_pasta = ['' for i in range(nApes)]
        buytx = ['' for i in range(nApes)]
        approvetx_pasta = ['' for i in range(nWallets)]
        approvetx = ['' for i in range(nWallets)]
        go_through = [False for i in range(nApes + nWallets)]


        # BEP20 token standard
        router_contract = self.web3.eth.contract(address=snipe_parameters['router'], abi=self.swapABI)

        async def _snipe_handler(client, message):

            try:
                # Try to find the contract through the text
                tokenToBuy = self.web3.toChecksumAddress(re.findall(pattern, message.text)[0])
            except IndexError:
                # Cannot find it in the text, status update
                self.active_snipes[snipe_chat_ID]['last_update'] = time.strftime('%H:%M:%S')

                tokenToBuy = None
            except:
                # Any other case, status update
                try:
                    # If the message is media could be find in the caption
                    tokenToBuy = self.web3.toChecksumAddress(re.findall(pattern, message.caption)[0])
                except:
                    # If none are found, update message
                    # TODO: add user timezone support on the larger SPICEMIX ecosystem
                    self.active_snipes[snipe_chat_ID]['last_update'] = time.strftime('%H:%M:%S')
                    tokenToBuy = None
                    """try:
                        # If not found, tries to find it from the pic through CV
                        # TODO: thoroughly test this bit with more case examples
                        path = self.user_app.download_media(message.photo.file_id)
                        img = cv2.imread(path)
                        text = ''.join(pytesseract.image_to_string(img).split())
                        print(text)
                        tokenToBuy = self.web3.toChecksumAddress(re.findall(pattern, text)[0])
                        print(tokenToBuy)
                    except AttributeError:"""  # ML of addy from image, to add

            # After these checks, if a token was found in the posts, buy it
            if tokenToBuy is not None:

                # Right after contract is detected, remove handler to prevent any spamming
                self.user_app.remove_handler(*self.active_snipes[snipe_chat_ID]['_handler'])

                # SAFESNIPE OPTION, will check for honeypot first if it is turned on
                if safesnipe is True:
                    tokenContractABI = self.web3.eth.contract(tokenToBuy, abi=self.tokenABI)

                    is_honeypot, report = await self._is_honeypot(
                        tokenToBuy, honeypot_default, router_contract, tokenContractABI)

                    if is_honeypot:
                        # Bot calls honeypot, cancel snipe and inform the user
                        await self._cancel_snipe(snipe_chat_ID)

                        # Send user message
                        msg = 'The sniper order was cancelled because the token was flagged as fraudulent.\n' \
                              'Honeypot checker report: '
                        msg += report + '\n\n'
                        msg += '[Chart for the token](https://poocoin.app/tokens/{}).'.format(
                            tokenToBuy)

                        # Sending report pasta
                        await self.currybot.send_message(self.userID, msg, parse_mode='markdown')
                        return

                # For regular sniper orders, or when token is not a honeypot, proceeds as usual

                # Buying
                routing = [pairing, tokenToBuy]
                expTime = int(time.time()) + transactionRevertTime
                nonces = [self.web3.eth.get_transaction_count(addy) for addy in self.addies[:nApes]]
                for i in range(nApes):
                    pcstx = router_contract.functions.swapExactETHForTokens(
                        0,
                        # Set to 0 or specify min number of tokens - setting to 0 just buys X amount of token at its current price for whatever BNB specified
                        routing,
                        sendTo[i],
                        expTime
                    ).buildTransaction({
                        'from': self.addies[i],
                        'value': amounts[i],
                        # This is the Token(BNB) amount you want to Swap from
                        'gas': snipe_parameters['gasamount'],
                        'gasPrice': self.web3.toWei(snipe_parameters['gasprice'], 'gwei'),
                        'nonce': nonces[i],
                    })

                    try:
                        signed_txn = self.web3.eth.account.sign_transaction(pcstx, self.pkeys[i])
                        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)  # BUY THE TOKEN
                    except:
                        buytx_pasta[i] = 'Buy transaction #{} failed.\n'.format(i + 1)
                        buytx[i] = None
                        go_through[i] = True  # Transaction failing means dont have to wait for it
                    else:
                        buytx_pasta[i] = '[Boughted #{}](https://bscscan.com/tx/{}).\n'.format(i + 1, tx_hash.hex())
                        buytx[i] = tx_hash.hex()

                tokenContractABI = self.web3.eth.contract(tokenToBuy, abi=self.tokenABI)
                # Approving
                for i in range(nWallets):
                    spender = snipe_parameters['router']
                    max_amount = self.web3.toWei(2 ** 64 - 1, 'ether')
                    # Approve is sent immediately after sending the ape in tx, so the nonce will be outdated, need to add one more

                    tx = tokenContractABI.functions.approve(spender, max_amount).buildTransaction({
                        'from': self.addies[i],
                        'nonce': nonces[i] + 1
                    })

                    try:
                        signed_txn = self.web3.eth.account.sign_transaction(tx, self.pkeys[i])
                        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    except:
                        approvetx_pasta[i] = 'Approve transaction #{} failed.\n'.format(i + 1)
                        # Although it will most likely be unable to sell, it is specified as true
                        approvetx[i] = None
                        go_through[nApes - 1 + i] = True
                    else:
                        approvetx_pasta[i] = '[Approved #{}](https://bscscan.com/tx/{}).\n'.format(i + 1, tx_hash.hex())
                        approvetx[i] = tx_hash.hex()

                # Getting the chat name that was sniped for report pasta
                try:
                    _chat = await self.user_app.get_chat(snipe_chat_ID)
                    name = '@' + _chat.username
                except:
                    name = ''
                    msg = 'Snipe order executed for `{}`\n\n'.format(snipe_chat_ID)
                else:
                    msg = 'Snipe order executed for `{}` {}\n\n'.format(snipe_chat_ID, name)

                # Transactions for report pasta
                for line in buytx_pasta:
                    msg += line
                for line in approvetx_pasta:
                    msg += line

                msg += '\n[Chart for your token](https://poocoin.app/tokens/{}).\n'.format(tokenToBuy)

                if snipe_parameters['moonbag'] != 0:
                    # If the moonbag was set, share it on the snipe report
                    msg += 'Predefined moonbag of {}%.'.format(snipe_parameters['moonbag'])

                # Sending report pasta
                await self.currybot.send_message(self.userID, msg, parse_mode='markdown')


                # AUTOSELLS WITH TIME DELAY
                if snipe_parameters['selldelay'] is not None:
                    # Check that all approve tx have gone thru, if some of them failed (None value) that wallet will
                    # not sell
                    for i in range(len(buytx)):
                        try:
                            self.web3.eth.wait_for_transaction_receipt(buytx[i], timeout=12)
                        except:
                            # Transaction wasn't mined or otherwise not confirmed. Balance will be checked later so it
                            # is not an issue
                            pass
                    for i in range(len(approvetx)):
                        try:
                            self.web3.eth.wait_for_transaction_receipt(approvetx[i], timeout=12)
                        except:
                            # Transaction wasn't mined or otherwise not confirmed
                            pass

                    t_start = time.time()
                    # This is the maximum amount each of the wallets can sell - simply an upper bound, not necessarily
                    # the max tx per se
                    maxtx = await self._get_maximum_tx(tokenToBuy, tokenContractABI, router_contract, pairing, nWallets)
                    maxtx = int(maxtx)
                    print(maxtx)

                    if maxtx == 0:
                        # Unable to sell, inform user that they will have to check it manually
                        msg = 'Unable to sell as the detected maximum transaction was 0. Please, try selling manually.'
                        await self.currybot.send_message(self.userID, msg)

                        # Remove the allocated main balance, minus the gas reserved for selling
                        sniping_gas = snipe_parameters['gasamount'] * snipe_parameters['gasprice'] / 10 ** 9
                        self.allocated_main_balance -= self.active_snipes[snipe_chat_ID]['amounts'][0] + 2 * sniping_gas

                        # Remove the active snipe
                        del self.active_snipes[snipe_chat_ID]
                        return

                    # Rest of selling parameters
                    moonbag = snipe_parameters['moonbag']
                    gasprice = self.gas_multiplier * self.web3.toWei('7', 'gwei')
                    selltx = []
                    msg = 'Autosell order executed for `{}` {}\n\n'.format(snipe_chat_ID, name)

                    # Wait for the specified amount of time - discounting the amount that was spent finding max tx
                    time_elapsed = time.time() - t_start
                    time_sleep = snipe_parameters['selldelay'] - time_elapsed
                    print(time_sleep)
                    if time_sleep >= 0:
                        # For non negative sleep values
                        await asyncio.sleep(time_sleep)

                    # Proceed to the dump
                    for i in range(nWallets):
                        print('recommence the dumps')
                        # Dumping each wallet, in order
                        balance = tokenContractABI.functions.balanceOf(self.addies[i]).call()
                        balance_sell = int(balance * (100 - moonbag) / 100)
                        print('balance to sell: {}'.format(balance_sell))
                        nonce = self.web3.eth.get_transaction_count(self.addies[i], 'pending')

                        # Adding to pasta
                        if i == 0:
                            msg += 'Main wallet breakdown:\n'
                        else:
                            msg += 'Wallet {} breakdown:\n'.format(i+1)

                        if balance == 0:
                            # Wallet holds none, skip to next wallet, and inform user accordingly
                            msg += 'Holds no tokens, unable to sell.\n\n'
                            continue

                        if balance_sell <= maxtx:
                            # Can just dump all the stack at once
                            try:
                                # Sell transaction, which might still fail, are made with half the buying gas
                                pcstx = router_contract.functions. \
                                    swapExactTokensForETHSupportingFeeOnTransferTokens(
                                    balance_sell, 0,
                                    [tokenToBuy, pairing],
                                    self.addies[i],
                                    int(time.time()) + transactionRevertTime
                                ).buildTransaction({
                                    'from': self.addies[i],
                                    'gasPrice': gasprice,
                                    'nonce': nonce
                                })
                            except Exception as e:
                                # Can't sell, inform the user but continue trying on later ones
                                msg += 'Encountered an error selling: {}\n'.format(e)
                                cant_sell = [True]
                            else:
                                # Transaction is at least possible
                                try:
                                    signed_txn = self.web3.eth.account.sign_transaction(pcstx, self.pkeys[i])
                                    tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                                except Exception as e:
                                    # In case it fails here, same fail message
                                    msg += 'Encountered an error selling: {}\n'.format(e)
                                    selltx.append(None)
                                    cant_sell = [True]
                                else:
                                    # Sell transaction got sent, might still fail when mining
                                    msg += '[Solded](https://bscscan.com/tx/{}).\n'.format(tx_hash.hex())
                                    selltx.append(tx_hash.hex())
                                    cant_sell = [False]

                        else:
                            # Need to dump in waves, a number of times to sell
                            n_sells = math.ceil(balance_sell/maxtx)
                            cant_sell = [False for i in range(n_sells)]
                            for j in range(n_sells):
                                # Dump each of these times
                                if j == n_sells - 1:
                                    # Last dump, sell remaining tokens
                                    maxtx = int(balance_sell - maxtx * (n_sells - 1))
                                try:
                                    # Sell transaction, which might still fail, are made with half the buying gas
                                    pcstx = router_contract.functions. \
                                        swapExactTokensForETHSupportingFeeOnTransferTokens(
                                        maxtx, 0,
                                        [tokenToBuy, pairing],
                                        self.addies[i],
                                        int(time.time()) + transactionRevertTime
                                    ).buildTransaction({
                                        'from': self.addies[i],
                                        'gasPrice': gasprice,
                                        'nonce': nonce + j
                                    })
                                except Exception as e:
                                    # Can't sell, inform the user but continue trying on later ones
                                    msg += 'Encountered error on sell #{}: {}\n'.format(j + 1, e)
                                    cant_sell[j] = True
                                else:
                                    # Transaction is at least possible
                                    try:
                                        signed_txn = self.web3.eth.account.sign_transaction(pcstx, self.pkeys[i])
                                        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                                    except Exception as e:
                                        # In case it fails here, same fail message
                                        msg += 'Encountered error on sell #{}: {}\n'.format(j + 1, e)
                                        selltx.append(None)
                                        cant_sell[j] = True
                                    else:
                                        # Sell transaction got sent, might still fail when mining
                                        msg += '[Solded #{}](https://bscscan.com/tx/{}).\n'.format(j + 1, tx_hash.hex())
                                        selltx.append(tx_hash.hex())

                        if all(cant_sell):
                            # Could not sell a single one, inform the user
                            msg += 'The program was not able to sell any of the tokens. You should check it manually.'
                            await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

                        if any(cant_sell):
                            # Could not sell some
                            msg += 'The program was not able to sell some tokens'
                            await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

                    if moonbag != 0:
                        if nWallets > 1:
                            wallets = ' {} wallets'.format(nWallets)
                        else:
                            wallets = ' the main wallet'
                        msg += '\nLeft a {}% moonbag on'.format(moonbag) + wallets

                    # Send the message
                    await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

                    # Add final message of estimated profit
                    msg = 'Autosell report for `{}` {}:\n'.format(snipe_chat_ID, name)
                    #profit = await self._calculate_profit(buytx, selltx)
                    #msg += 'Estimated profit: **{:.5f} BNB**'.format(profit)
                    #await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

                # Remove the allocated main balance, minus the gas reserved for selling
                sniping_gas = snipe_parameters['gasamount'] * snipe_parameters['gasprice'] / 10 ** 9
                self.allocated_main_balance -= self.active_snipes[snipe_chat_ID]['amounts'][0] + 2 * sniping_gas

                # Remove the active snipe
                del self.active_snipes[snipe_chat_ID]

        self.active_snipes[snipe_chat_ID]['_handler'] = self.user_app.add_handler(MessageHandler(
            _snipe_handler,
            filters=pyrogram.filters.chat(snipe_chat_ID) & ~pyrogram.filters.user(snipe_parameters['blacklistbots'])
        ))

    async def _is_honeypot(self, tokenToBuy, honeypot_default, router_contract, tokenContractABI):
        """Performs a simple check to fastly determine if the token is a honeypot or not

        :param tokenToBuy: checksum contract address of the token
        :param honeypot_default: bool, flag to default to
        :param router_contract: smart contract functions of the router where the token is listed
        :param tokenContractABI: smart contract functions of the token to buy
        :return: is_honeypot, boolean, whether the token was flagged as honeypot or not
                 report, short message about how the decision was made
        """

        # BLOCKS: first check latest block, then check pending
        holder = None
        blocktx = self.web3.eth.get_block('latest', full_transactions=True)
        firstblock = blocktx['number']
        i = 0

        # While loop that will break once a holder is found or all tx on latest and pending blocks are checked
        while holder is None and i < 2:
            # Get the transactions from the block and iterate through them
            for tx in blocktx['transactions']:
                # Check if the tx is interacting with the contract address of the token, and cop the sender as holder
                if tx['to'] == tokenToBuy:
                    holder = tx['from']
                    balance = tokenContractABI.functions.balanceOf(holder).call()
                    if balance > 0:
                        # Holder has some tokens in his balance, so it is possible to check for honeypot
                        try:
                            # Simulate sell transaction
                            simtx = router_contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                                int(balance / 10), 0,
                                [tokenToBuy, self.pairing],
                                holder,
                                (int(time.time()) + 1000000)
                            ).buildTransaction({
                                'from': holder,
                                'gasPrice': self.web3.toWei('5', 'gwei'),
                                'nonce': self.web3.eth.get_transaction_count(holder, 'pending')
                            })
                        except Exception as e:
                            print('HONEYPOT EXCEPTION: {}'.format(e))
                            # Cant sell, its honeypot
                            is_honeypot = True
                            report = 'honeypot detected as [this wallet](https://bscscan.com/address/{}) ' \
                                     'is unable to sell.'.format(holder)
                            return is_honeypot, report
                        else:
                            return False, None
                    else:
                        # Can't test for honeypot, continue iterating
                        holder = None

            # Nothing found
            i += 1
            # Loop done, return default values
            if i == 2:
                if honeypot_default is False:
                    return False, None
                elif honeypot_default is True:
                    return True, 'could not test for honeypot, defaulted to TRUE. Blocks tested: {}, {}'.format(
                        firstblock, secondblock
                    )
            # Last block iterated over, jump on to the pending transactions then
            blocktx = self.web3.eth.get_block('pending', full_transactions=True)
            secondblock = blocktx['number']

    async def set_up_snipe(self, params, safe=False):
        """Sets up the sniper order following the defined parameters

        :param params: dictionary containing the sniping parameters
        :param safe: bool, whether it is a safesnipe order or a regular order, defaults to False for regular snipe order
        """

        try:
            # ['@telegramgroup', 'parameter1 value, value, value', 'parameter2 value', 'parameter3 value']
            snipe_chat = params[0]
            try:
                # User provided the chat ID directly, WITH THE MINUS SIGN
                snipe_chat_ID = int(snipe_chat)
            except ValueError:
                # User provided the group, get the corresponding ID
                _chat = await self.user_app.get_chat(snipe_chat[1:])
                snipe_chat_ID = _chat.id

            if snipe_chat_ID in self.active_snipes.keys():
                # That chat is already being sniped
                msg = 'The chat you provided is already being sniped. You may check on active orders by typing ' \
                      '/activeSnipes, and cancel them using /cancelSnipe.'
                await self.currybot.send_message(self.userID, msg)
                return

            # Fill up the parameters
            # Some of these None values will change to default ones once the sniper is set up
            snipe_parameters = {
                'amounts': None,
                'holdwallets': None,
                'router': None,
                'pairing': None,   # self.web3.toChecksumAddress("0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c")
                'reverttime': None,
                'blacklistbots': None,
                'gasamount': 1000000,
                'gasprice': self.gas_multiplier * 33,
                'selldelay': None,
                'moonbag': None,
                'safesnipe': False,
                'honeydefault': None
            }
            # Change dictionary values with those specified
            for parameter in params[1:]:
                name = parameter.split(' ')[0].lower()
                values = ''.join(parameter.split(' ')[1:]).split(',')
                snipe_parameters[name] = values
        except:
            await self.currybot.send_message(self.userID, 'Invalid command! Type /snipeHelp for more information.')
            return

        # Individually setting each of them up:

        # AMOUNTS PARAMETER
        try:
            snipe_parameters['amounts'] = [float(i) for i in snipe_parameters['amounts']]
        except ValueError:
            await self.currybot.send_message(self.userID, 'The ape-in amounts you provided are invalid. '
                                                          'Type /snipeHelp for more information.')
            return

        # HOLDWALLETS PARAMETER
        if snipe_parameters['holdwallets'] is None:
            snipe_parameters['holdwallets'] = 1
        else:
            try:
                snipe_parameters['holdwallets'] = int(snipe_parameters['holdwallets'][0])
            except ValueError:
                await self.currybot.send_message(self.userID, 'The holdwallets value you provided is invalid. '
                                                              'Type /snipeHelp for more information.')
                return

        # PAIRING PARAMETER
        if snipe_parameters['pairing'] is None:
            # If no pairing is defined, defaults to a BNB pairing
            snipe_parameters['pairing'] = self.pairing
            # ON BSC: self.web3.toChecksumAddress("0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c")
        else:
            # A pairing is defined
            try:
                # See if what was provided was a contract address
                snipe_parameters['pairing'] = self.web3.toChecksumAddress(snipe_parameters['pairing'][0])

            except ValueError:
                # It was not a contract address, try to see if its a supported one
                try:
                    snipe_parameters['pairing'] = self.supported_pairings[snipe_parameters['pairing'][0].lower()]

                except KeyError:
                    await self.currybot.send_message(self.userID, 'The pairing value you provided is invalid. '
                                                                  'Type /snipeHelp for more information.')
                    return
            except:
                await self.currybot.send_message(self.userID, 'The pairing value you provided is invalid. '
                                                              'Type /snipeHelp for more information.')
                return

            await self.currybot.send_message(self.userID, 'You selected a non-BNB pairing. Bear in mind '
                                                          'that the program will not check if you have the required '
                                                          'balance.')

        # ROUTER PARAMETER
        if snipe_parameters['router'] is None:
            snipe_parameters['router'] = self.router
        else:
            try:
                snipe_parameters['router'] = self.routers[snipe_parameters['router'][0]]
            except:
                await self.currybot.send_message(self.userID, 'The router you provided is invalid. '
                                                              'Type /snipeHelp for more information.')
                return

        # REVERT TIME PARAMETER
        if snipe_parameters['reverttime'] is None:
            snipe_parameters['reverttime'] = 20  # DEFAULT REVERT TIME
        else:
            try:
                snipe_parameters['reverttime'] = float(snipe_parameters['reverttime'][0])
            except:
                await self.currybot.send_message(self.userID, 'The revert time you provided is invalid. '
                                                              'Type /snipeHelp for more information.')
                return

        # BLACKLISTBOTS PARAMETER
        if snipe_parameters['blacklistbots'] is None:
            snipe_parameters['blacklistbots'] = self.blacklisted_accounts
        else:
            try:
                blacklisted = self.blacklisted_accounts[:]
                for account in snipe_parameters['blacklistbots']:
                    blacklisted.append(account[1:])
                snipe_parameters['blacklistbots'] = blacklisted
            except:
                await self.currybot.send_message(self.userID, 'The blacklisted list you provided is invalid. '
                                                              'Type /snipeHelp for more information.')
                return

        # SELLDELAY PARAMETER
        # This represents the amount of time the program waits after buy and approve have been confirmed to dump
        # The default value of None means that the program will not autosell
        if snipe_parameters['selldelay'] is not None:
            try:
                snipe_parameters['selldelay'] = int(snipe_parameters['selldelay'][0])
            except:
                await self.currybot.send_message(self.userID, 'The selldelay value you provided is invalid. '
                                                              'Type /snipeHelp for more information.')
                return
            else:
                if snipe_parameters['selldelay'] < 0:
                    # Cant take negative values
                    await self.currybot.send_message(self.userID, 'The selldelay value you provided is invalid. '
                                                                  'Type /snipeHelp for more information.')
                    return

        # MOONBAG PARAMETER
        # Percentage of the balance to keep after selling, be it time based or user triggered
        if snipe_parameters['moonbag'] is not None:
            try:
                snipe_parameters['moonbag'] = int(snipe_parameters['moonbag'][0])
            except:
                await self.currybot.send_message(self.userID, 'The moonbag value you provided is invalid. '
                                                              'Type /snipeHelp for more information.')
                return
            else:
                if snipe_parameters['moonbag'] < 0 or snipe_parameters['moonbag'] > 100:
                    # Cant take negative values, or values greater than 100%
                    await self.currybot.send_message(self.userID, 'The moonbag value you provided is invalid. '
                                                                  'Type /snipeHelp for more information.')
                    return
        else:
            # Moonbag not defined, aka value equals zero:
            snipe_parameters['moonbag'] = 0

        # SAFESNIPE AND HONEY DEFAULT VALUE
        if safe:
            snipe_parameters['safesnipe'] = True
            if snipe_parameters['honeydefault'] is None:
                snipe_parameters['honeydefault'] = True
            elif snipe_parameters['honeydefault'][0].lower() == 'false':
                snipe_parameters['honeydefault'] = False
            else:
                await self.currybot.send_message(self.userID, 'The honey default value you provided is invalid. '
                                                              'Type /snipeHelp for more information.')
                return

        # TO BE ADDED IN THE FUTURE ??
        sniping_gas = self.gas_multiplier * snipe_parameters['gasamount'] * snipe_parameters['gasprice'] / 10 ** 9
        needed_balance = sum(snipe_parameters['amounts']) + \
                         len(snipe_parameters['amounts']) * sniping_gas

        # Another sniping_gas will be needed in each of the wallets that will hold, for selling, whether time delayed
        # or user triggered
        needed_balance += snipe_parameters['holdwallets'] * sniping_gas

        available_balance = await self._get_BNB_balance(self.main_addy)
        # Available balance is the balance in the main wallet minus the allocated balance, and 0.03 for emergency gas
        available_balance -= self.allocated_main_balance + 0.03

        if needed_balance > available_balance:
            msg = 'Insufficient balance for your order! Try /resetbalance, or ' \
                  'add more funds by sending BNB to:\n`{}`'.format(self.main_addy)
            await self.currybot.send_message(self.userID, msg, parse_mode='markdown')
            return

        # There is enough balance to process order, send to proxy wallets
        amounts_to_send = [buy + sniping_gas for buy in snipe_parameters['amounts'][1:] if buy > 0]
        # Add to that the required gas for selling in each of the proxy wallets that will hold
        for i in range(snipe_parameters['holdwallets']-1):
            amounts_to_send[i] += sniping_gas
        await self._send_proxy_balances(amounts_to_send)

        # Main balance that will be allocated for this snipe is the amount to buy plus twice the sniping gas
        self.allocated_main_balance += snipe_parameters['amounts'][0] + 2 * sniping_gas

        # Allocate this snipe in the active snipes list
        self.active_snipes[snipe_chat_ID] = snipe_parameters

        if safe:
            # Safesnipe order being placed
            await self._snipe(snipe_chat_ID, snipe_parameters, safesnipe=True)

            msg = 'Your safesnipe order is placed! You may check on its status by typing /activeSnipes.'
            await self.currybot.send_message(self.userID, msg)

        else:
            # Regular sniper order being placed
            await self._snipe(snipe_chat_ID, snipe_parameters)

            msg = 'Your sniper order is placed! You may check on its status by typing /activeSnipes.'
            await self.currybot.send_message(self.userID, msg)

    async def get_active_snipes(self, params):
        """Shows the user a message about all the active snipes there are"""

        if len(self.active_snipes) == 0:
            await self.currybot.send_message(self.userID, 'You have no active snipes.')
        else:
            msg = 'Active snipes:\n\n'
            for active_snipe in self.active_snipes.keys():
                try:
                    # Try to get the group name
                    _chat = await self.user_app.get_chat(active_snipe)
                    name = _chat.username
                except:
                    # There is no group name, post the ID
                    if self.active_snipes[active_snipe]['safesnipe'] is True:
                        msg += 'Safesnipe order for `{}`:\n'.format(active_snipe)
                    else:
                        msg += 'Snipe order for `{}`:\n'.format(active_snipe)
                else:
                    # There is a group name, post it alongside the ID
                    if self.active_snipes[active_snipe]['safesnipe'] is True:
                        msg += 'Safesnipe order for `{}` @{}:\n'.format(active_snipe, name)
                    else:
                        msg += 'Snipe order for `{}` @{}:\n'.format(active_snipe, name)

                # Amounts being sniped
                amounts = self.active_snipes[active_snipe]['amounts']
                _msg = 'Snipe amounts: {:.3f}'.format(amounts[0])
                for amount in self.active_snipes[active_snipe]['amounts'][1:]:
                    _msg += ', {:.3f}'.format(amount)
                msg += _msg + '.\n'

                # Wallets that are left holding the bag
                holdwallets = self.active_snipes[active_snipe]['holdwallets']
                if holdwallets > 1:
                    msg += 'To be sent to {} wallets.\n'.format(holdwallets)

                # Amount of time to wait before selling - time triggered sell
                selldelay = self.active_snipes[active_snipe]['selldelay']
                if selldelay is not None:
                    msg += 'To be sold {} seconds after confirmation.\n'.format(selldelay)

                # Amount to not sell and leave as a moonbag, as percentage of the supply you captured
                moonbag = self.active_snipes[active_snipe]['moonbag']
                if moonbag != 0:
                    msg += 'Leaving a {}% moonbag after selling.\n'.format(moonbag)

                # Adding the last update to reassure the user that their sniper is live
                try:
                    last_update = self.active_snipes[active_snipe]['last_update']
                except KeyError:
                    last_update = 'NONE'

                msg += 'Last update: {}\n\n'.format(last_update)

            await self.currybot.send_message(self.userID, msg)



    async def cancel_snipe(self, params):
        """Cancels an active snipe, user must provide either the groupID or the group name"""

        try:
            snipe_to_cancel = params[0]
            try:
                # User provided the chat ID directly
                snipe_chat_ID = int(snipe_to_cancel)
                chat_name = ''
            except ValueError:
                # User provided the group, get the corresponding ID
                _chat = await self.user_app.get_chat(snipe_to_cancel[1:])
                snipe_chat_ID = _chat.id

            # Cancelling snipe method
            await self._cancel_snipe(snipe_chat_ID)

            # Inform the user
            msg = 'Your order was cancelled and funds will be refunded to the main wallet. Type /activeSnipes to see ' \
                  'a quick rundown of the groups you are sniping.'
            await self.currybot.send_message(self.userID, msg)

        except KeyError:
            msg = 'The group you provided is not in the active snipes! Type /activeSnipes to see a quick rundown' \
                  'of the groups you are sniping.'
            await self.currybot.send_message(self.userID, msg)
            return

        except:
            await self.currybot.send_message(self.userID, 'Invalid command! Type /help for more information.')
            return

    async def _cancel_snipe(self, snipe_chat_ID):
        """Cancels the specified sniper order

        :param snipe_chat_ID: chat ID of the snipe to cancel
        """
        # Remove handler, or try to do so - might have been remove earlier during a snipe order execution
        try:
            self.user_app.remove_handler(*self.active_snipes[snipe_chat_ID]['_handler'])
        except:
            pass

        # Gas allocated for each snipe
        snipe_parameters = self.active_snipes[snipe_chat_ID]
        sniping_gas = snipe_parameters['gasamount'] * snipe_parameters['gasprice'] / 10 ** 9

        # Remove the allocated main balance, the amount to buy and 2x the gas used to buy, as some is reserved to sell
        self.allocated_main_balance -= self.active_snipes[snipe_chat_ID]['amounts'][0] + 2 * sniping_gas

        # Amounts to send back from each of the proxy wallets
        amounts_to_send = [buy + sniping_gas for buy in snipe_parameters['amounts'][1:] if buy > 0]
        for i in range(snipe_parameters['holdwallets']-1):
            # Adding the extra gas that gets allocated in each of the proxy wallets for selling
            amounts_to_send[i] += sniping_gas
        await self._send_proxy_balances_back(amounts_to_send)

        # Delete the dictionary entry
        del self.active_snipes[snipe_chat_ID]

    async def change_gas_multiplier(self, params):
        """Change the gas multiplier for periods of high network congestion"""
        try:
            self.gas_multiplier = float(params[0])
        except:
            msg = 'You did not provide any value. The current gas multiplier is: {:.2f}x'.format(self.gas_multiplier)
            await self.currybot.send_message(self.userID, msg)
        else:
            msg = 'The new gas multiplier is {:.2f}x'.format(self.gas_multiplier)
            await self.currybot.send_message(self.userID, msg)

    async def help(self, params):
        """Sends the user a guide message on all available parameters"""

        msg = 'This is a list of all the supported commands:\n\n' \
              '/start: sets up or connects to your personal telegram client. You will need to call this the first time ' \
              'you interact with the CurrySniperBot, and every time you get notified of a new update.\n\n' \
              '/balance: shows the balance of all the wallets under your control.\n\n' \
              '/resetBalance: sends the excess balance from the proxy wallets back to the main wallet. Intended as a ' \
              'last resort feature if something goes wrong. You will not be able to reset balance if you have any ' \
              'active snipes.\n\n' \
              '/personalWallet: allows you to set up, check or change your personal wallet address, a wallet that is ' \
              'under your sole control and that you can easily send funds back to.\n\n' \
              '/redeem: sends the specified amount of beans back to your personal wallet.\n\n' \
              '/sneed: shows the sneed phrase used to generate all the wallets under your control, to easily import ' \
              'them into a MetaMask/Trust Wallet account.\n\n' \
              '/getGroupID: gets the unique groupID of the group you next post a message to, useful when sniping ' \
              'private groups.\n\n' \
              '/snipe: the sniping order command.\n\n' \
              '/safesnipe: a safer alternative to the sniping order command that checks if the token is a honeypot ' \
              'at the time of buying, and will cancel the order in that case.\n\n' \
              '/sell: when __replying__ to a snipe report, will sell that token, avoiding max transactions. You can ' \
              'override the moonbag parameter of the snipe by specifying what amount of tokens you would like to' \
              'sell, so __/sell 90__ would sell 90% of your holdings, leaving a 10% moonbag.\n\n' \
              '/snipeHelp: shows a help message for the snipe command.\n\n' \
              '/safesnipeHelp: shows a help message for the safesnipe command.\n\n' \
              '/activeSnipes: shows a quick rundown of all the active snipes.\n\n' \
              '/cancelSnipe: cancels an active snipe. You may provide the @TelegramGroup or the unique groupID.\n\n' \
              '/gasMultiplier: increases the gas spent by this multiplier, defaults to 1. It is advisable to increase it ' \
              'during periods of high network congestion.\n\n' \
              '/disclaimer: shows a disclaimer message about sniper usage.\n\n' \
              '/help: shows this message.\n\n' \
              '/restart: will restart the program fully. Use it for loading new updates when you get notified of ' \
              'them.\n\n'\
              '/about: shows a message with information about the product.'

        await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

    async def snipe_help(self, params):
        """Sends the user a guide message on all the available snipe parameters"""

        # TODO: similarly to router, add an option for a BUSD pairing definition

        msg = 'A sniper command is executed as follows:\n' \
              '/snipe @TelegramGroup; amounts __value__; parameter2 __value__; parameter3 __value__; ...\n\n' \
              'Where @TelegramGroup is the group you wish to snipe. You may also use the groupID instead of a ' \
              '@TelegramGroup, which can be obtained with the command /getGroupID. This is useful in the case of ' \
              'private groups. If you set up a snipe on a public group that went private afterwards, you do not need ' \
              'to worry as its unique groupID is what is being sniped. **You need to be a member of the group you ' \
              'want to snipe with the account you set up the API for.**\n\n' \
              'After setting up which group to snipe, you may then tweak the different parameters related to your ' \
              'order. Of these, only the **__amounts__ parameter needs to be specified**, the rest of them are optional. ' \
              'Each of these parameters needs to be defined as shown above: providing the parameter name, followed by ' \
              'a whitespace, and then the specified value. Defined parameters needs to be separated by a semi ' \
              'colon (;). The list of supported parameters is the following:\n\n' \
              '>__--amounts--__: amount of BNB to buy with. If you wish to do several ape-ins, these amounts need to be ' \
              'separated by commas (eg: amounts 0.1, 0.2, 0.3). Each of the ape-ins will be performed with a different ' \
              'wallet, to try and avoid max tx limits.\n\n' \
              '>__--holdWallets--__: number of wallets to hold tokens with, defaults to just the main wallet. The sniper ' \
              'will automatically send tokens to this number of wallets when buying. Use it alongside the __amounts__ ' \
              'parameter to avoid max tx and max hold restrictions and capture a larger % of the supply.\n\n' \
              '>__--moonbag--__: percentage of your holdings you would like to keep after selling, be it time ' \
              'delayed or triggered by a /sell command.\n\n' \
              '>__--sellDelay--__: when defined, amount of time in seconds the program will wait after buying has ' \
              'been confirmed to automatically sell.\n\n' \
              '>__--router--__: by default, buys into pancakeswap V2 liquidity pools. On the rare instance that you find a ' \
              'launch on apeswap, you may set this as __router apeswap__.\n\n' \
              '>__--revertTime--__: maximum amount of time you are willing to wait before the tx is cancelled. Defaults ' \
              'to 20 seconds, you may increase this during periods of high network congestion. Because every ape-in ' \
              'gets performed with high gas, this parameter should not cause any issues. If you got rekted by this, ' \
              'please contact me @CurryDev.\n\n' \
              '>__--blacklistBots--__: because the CurrySniper reads the message feed of a group, you may want to avoid ' \
              'messages from bots. CurrySniper automatically ignores messages from @MissRose_bot, @shieldy_bot, ' \
              '@BanhammerMarie2_bot, @combot and @GroupHelpBot. You may add more to this list for **just the sniper ' \
              'order being placed** like this:\n__blacklistBots @bot1, @bot2, @bot3__\n\n' \
              '**MAKE SURE THE TELEGRAM CHAT IS MUTED BEFORE PLACING ANY SNIPER ORDER**\n' \
              '__Automatic muted-chat detection will be added on future updates__.'

        # '>__--pairing--__: by default, buys in with BNB. On the rare instance that you find a non-BNB token ' \
        # 'pairing, you may change it to BUSD or USDT:\n' \
        # '__pairing BUSD__ or __pairing USDT__\n' \
        # '**The program will not check if you have the required balance for buying when you specify a different ' \
        # 'pairing. You also need to have the pairing token approved for spending.**\n\n' \

        await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

    async def safesnipe_help(self, params):
        """Sends the user additional info on a safesnipe command"""

        msg = 'A safesnipe command includes an additional layer of safety: it will try to determine if the token is a '\
              'honeypot by simulating a sell coming from a wallet that holds it. It will try to look for that holder ' \
              'in the latest and pending blocks. If the token is in fact a honeypot and the holder that is found ' \
              'happens to be a whitelisted wallet, the program will not flag a honeypot as such (I suspect that to be ' \
              'a rare event). If the launch is not hyped enough, it will be unable to find a wallet to simulate a ' \
              'sell with, and it will not be possible to make a decision. For these cases, you may define a default ' \
              'behaviour by using:\n\n' \
              '>__--honeyDefault--__: defaults to true, meaning if no decision is made, it will assume the token is ' \
              'fraudulent. If you wish to take the risk, you may set this as __honeyDefault false__.\n\n' \
              'Besides this extra parameter, a safesnipe command is executed the same way as a /snipe command. You ' \
              'may type /snipeHelp for more information on how to set up a snipe command.'

        await self.currybot.send_message(self.userID, msg, parse_mode='markdown')


    async def disclaimer(self, params):
        """Sends the user a disclaimer message with tips on what to avoid and denying any responsibilities on my end"""

        msg = 'As a general rule of thumb, try to avoid Telegram groups that seem too botted: big members to total ' \
              'messages ratio, chats that have never been opened, high presence of jeety accounts... ' \
              'An **active** VC just before launch to answer the usual "wen moon" questions is often a good sing. ' \
              'Ideally, they should have at least a 10% VC members to total members ratio. More people on the VC ' \
              'obviously means more activity at the time of launch.\n\n' \
              'Setting up a sniper allows you to tweak a handful of parameters to avoid max transaction/ max hold' \
              'restrictions. This is a powerful tool, but only on the right hands. You can still buy into honeypots, ' \
              'have failed tx, or even end up buying the top if the launch wasn\'t __really__ fair. I know for a fact ' \
              'I have. You are the one responsible for placing snipes on legit launches, and tweaking the parameters ' \
              'accordingly.\n\n' \
              'As part of the CurryToolSuite (SPICEMIX), I plan on releasing an automatic daily curated list of ' \
              'snipeable launches. As a licensed CurrySniper, you will be able to get a subscription for a fee ' \
              '(price TBA). The idea is for it to automatically vet telegram groups and compile all crucial ' \
              'information: max buy, max wallet, and hopefully even __when__ to auto sell, leveraging all the data ' \
              'from __all__ snipes done.\n\n' \
              'If you have any questions about the product, feel free to ask me @CurryDev, and keep trade secrets off ' \
              'the main chat.'
        await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

    async def restart(self, params):
        """Exists the program, restart will be made by the pm2 handler"""
        await self.currybot.send_message(self.userID, 'Please, wait a couple seconds while the program restarts.')
        # Need a PM2 handler for the program to restart right after exiting
        sys.exit()


    async def about(self, params):
        """Sends a message with information about the product and the Curry Tool Suite"""

        # Generating and sending pasta
        msg = 'CurrySniper running on **{}**\n'.format(self.version)
        msg += 'Part of @DrCurry and the Curry Tool Suite (SPICEMIX). Building new tools for the blockchain to keep up '
        msg += 'with the ever-changing shitcoin scene.'
        await self.currybot.send_message(self.userID, msg, parse_mode='markdown')

    async def revoke_license(self):
        """Removes all active message handlers, especially the handlerGUI, revoking the user's license"""

        # The currybot hanlder is always present, remove it first
        self.currybot.remove_handler(*self.handlerGUI)
        # Then removes all the active handlers there might be
        for snipeID in self.active_snipes.keys():
            self.user_app.remove_handler(*self.active_snipes[snipeID]['_handler'])
        # And removes the ID handler if present
        try:
            self.user_app.remove_handler(*self.ID_handler)
        except:
            pass
        # Lastly, inform the user
        self.currybot.send_message(self.userID, 'Your license was revoked. Contact @CurryDev for more information.')

