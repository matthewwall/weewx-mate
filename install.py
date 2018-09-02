# installer for mate driver
# Copyright 2018 Matthew Wall

from setup import ExtensionInstaller

def loader():
    return MATEInstaller()

class MATEInstaller(ExtensionInstaller):
    def __init__(self):
        super(MATEInstaller, self).__init__(
            version="0.1",
            name='mate',
            description='Collect data from MATE3 solar controller',
            author="Matthew Wall",
            author_email="mwall@users.sourceforge.net",
            files=[('bin/user', ['bin/user/mate.py'])]
            )
