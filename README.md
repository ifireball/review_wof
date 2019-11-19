# review_wof
Code review wall-of-fame dasboard

## Development environment setup

1. Install Python 3 (Python 2 is not supported):

   ```
   yum install python36 python36-pip  # On CentOS 7
   ```

2. Install Python modules:

   ```
   python3 -m pip install --user -r requirements.txt
   ```

   Or if you have [pipx][1]:

   ```
   pipx install -r requirements.txt
   ```

## Running in production mode

With *pipenv* installed:

```
pipenv run gunicorn
```


[1]: https://pipxproject.github.io/pipx/
