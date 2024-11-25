import pathlib
import random


peoplePath = pathlib.Path('audios/people').resolve()
peopleAudios = [file.as_uri() for file in peoplePath.glob('*.mp3')]

audioDict = {'people': peopleAudios
            }

def getCrowdNoise(crowd):
    return random.choice(audioDict[crowd])