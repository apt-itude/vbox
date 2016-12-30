from setuptools import setup

setup(
    name='vbox',
    version='0.0.3',
    description='VirtualBox VM Management Tool',
    packages=['vbox'],
    entry_points={
        'console_scripts': [
            'vm = vbox.__main__:main'
        ]
    }
)
