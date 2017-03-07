from setuptools import setup,find_packages


setup(
    name='pyMSI',
    version='0.1',
    py_modules=['pyMSI'],
    include_package_data=True,
    packages = find_packages(),
    install_requires=[
        'click','matplotlib','numpy','pyimzml','scipy','scikit-image'
    ],
    entry_points='''
        [console_scripts]
        pymsi=cmds.pymsi_cmd:cli
    ''',
)
