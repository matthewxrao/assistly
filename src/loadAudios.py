import pathlib
import random

# All audios are from https://www.101soundboards.com/

humanPath = pathlib.Path('audios/humans').resolve()
humanAudios = [file.as_uri() for file in humanPath.glob('*.mp3')]

minionPath = pathlib.Path('audios/minion').resolve()
minionAudios = [file.as_uri() for file in minionPath.glob('*.mp3')]

dogPath = pathlib.Path('audios/dog').resolve()
dogAudios = [file.as_uri() for file in dogPath.glob('*.mp3')]

cowPath = pathlib.Path('audios/cow').resolve()
cowAudios = [file.as_uri() for file in cowPath.glob('*.mp3')]

audioDict = {'humans': humanAudios,
            'minions': minionAudios,
            'dogs': dogAudios,
            'cows': cowAudios
             
            }

def getCrowdNoise(crowd):
    return random.choice(audioDict[crowd])