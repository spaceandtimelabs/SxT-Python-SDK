from distutils.core import setup
setup(
  name = 'spaceandtime',         # How you named your package folder (MyLib)
  packages = ['spaceandtime'],   # Chose the same as "name"
  version = '0.0.2',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'Space and Time Python SDK', 
  author = 'Stephen Hilton',                   
  author_email = 'stephen.hilton@spaceandtime.io', 
  url = 'https://github.com/spaceandtimelabs/SxT-Python-SDK',    
  download_url = 'https://github.com/user/reponame/archive/v_01.tar.gz',    
  keywords = ['Space and Time', 'SXT', 'Python', 'SDK', 'Web3', 'Blockchain'],   
  install_requires=[            
          'validators',
          'beautifulsoup4',
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      #  either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" 
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   
    'Programming Language :: Python :: 3',     
    'Programming Language :: Python :: 3.10',
  ],
)