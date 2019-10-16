import asyncio
import os
import slack
from slack import RTMClient
import json
import logging

# create logger
logger = logging.getLogger('loggymclogface')
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

#TODO TOKEN = XXX
#TODO combine datastructures into a 'players' list with players objects
client = slack.WebClient(token=TOKEN)
PLAYERS = [
#    [ 'bob', 'slack user id' ],
]

CHANNEL_IDS = {
   # 'slack user id': 'slackbot channel w user',
}


CURRENT_TURN_POINTER = 2
PESTER_TASK = None

def get_users():
    client.users_list()
    xx =client.users_list()
    for d in xx.data['members']:
        print(d['name'], d['id'], d['group'])

async def heartbeat():
    # for testing
    while True:
        print('hb')
        await asyncio.sleep(1)

async def schedule_pester(wait_t, web_client, channel_id, user):
    await asyncio.sleep(wait_t)
    web_client.chat_postMessage(
                channel=channel_id,
                text=f'hey there <@{user}>, it looks like you havent made a move in {wait_t} seconds. This is a casual reminder.',
            )  

#def run_bot():
@RTMClient.run_on(event="message")
async def say_hello(**payload):
    global CURRENT_TURN_POINTER
    global PESTER_TASK
    data = payload['data']
    web_client = payload['web_client']
    name = data['username'] if 'username' in data else data.get('channel', None) 
    logger.info(f'{name} says {data["text"]}')
    if ('text' in data) and ('bot_id' not in data):
        channel_id = data['channel']
        if 'Hello' in data['text']:
            thread_ts = data['ts']
            user = data['user']

            web_client.chat_postMessage(
                channel=channel_id,
                text=f"Hi <@{user}>!",
                thread_ts=thread_ts
            )
            
        if 'reg' in data['text']:
            CHANNEL_IDS[data['user']] = channel_id
            with open('data.txt', 'w') as f:
                f.write(f'{data["user"]}: {channel_id}\n')
            web_client.chat_postMessage(
                channel=channel_id,
                text=f'registered <@{data["user"]}>',
            )  
        try:
            if 'start' in data['text']:
                web_client.chat_postMessage(
                    channel=CHANNEL_IDS[PLAYERS[CURRENT_TURN_POINTER][1]],
                    text=f'its your turn'
                )            
                if PESTER_TASK is not None:
                    PESTER_TASK.cancel()
                    PESTER_TASK = None
                PESTER_TASK = asyncio.ensure_future(schedule_pester(3600,
                                                            web_client,
                                                            CHANNEL_IDS[PLAYERS[CURRENT_TURN_POINTER][1]],
                                                            CHANNEL_IDS[PLAYERS[CURRENT_TURN_POINTER][0]]))
            if data['text'] in ['done', 'Done']:
                if PLAYERS[CURRENT_TURN_POINTER][1] == data['user']:
                    web_client.chat_postMessage(
                        channel=CHANNEL_IDS[PLAYERS[CURRENT_TURN_POINTER][1]],
                        text=f'your turn is done'
                    )
                    CURRENT_TURN_POINTER += 1
                    if CURRENT_TURN_POINTER == len(PLAYERS):
                        CURRENT_TURN_POINTER = 0
                    print(f'go {PLAYERS[CURRENT_TURN_POINTER][0]}!!!!')
                    web_client.chat_postMessage(
                        channel=CHANNEL_IDS[PLAYERS[CURRENT_TURN_POINTER][1]],
                        text=f'its your turn. the first few turns will be boring and quick!'
                    )
                    if PESTER_TASK is not None:
                        PESTER_TASK.cancel()
                        PESTER_TASK = None
                    PESTER_TASK = asyncio.ensure_future(schedule_pester(3600,
                                                                web_client,
                                                                CHANNEL_IDS[PLAYERS[CURRENT_TURN_POINTER][1]],
                                                                CHANNEL_IDS[PLAYERS[CURRENT_TURN_POINTER][0]]))
                else:
                    web_client.chat_postMessage(
                        channel=CHANNEL_IDS[data['user']],
                        text=f'stay engaged, it is not your turn'
                    )
            if 'skip' in data['text']:
                print('skipping: ', PLAYERS[CURRENT_TURN_POINTER][0])
                CURRENT_TURN_POINTER += 1
                if CURRENT_TURN_POINTER == len(PLAYERS):
                    CURRENT_TURN_POINTER = 0
                web_client.chat_postMessage(
                    channel=CHANNEL_IDS[PLAYERS[CURRENT_TURN_POINTER][1]],
                    text=f'its your turn'
                )
        except Exception as ex:
            print('exception!!!', ex)
            
#rtm_client = RTMClient(token=TOKEN)
#rtm_client.start()

if __name__ == '__main__':
    #get_users()
    LOOP = asyncio.get_event_loop()
    rtm_client = RTMClient(token=TOKEN)
#    asyncio.ensure_future(heartbeat())
    LOOP.run_until_complete(rtm_client.start())

#    run_bot()
