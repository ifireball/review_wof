# review_wof
Code review wall-of-fame dasboard

## Development environment setup

1. Install Python 3 (Python 2 is not supported):

   ```
   yum install python36 python36-pip  # On CentOS 7
   ```

2. Install [pipenv][1]:

   ```
   python3 -m pip install --user pipenv
   ```

   Or if you have [pipx][2]:

   ```
   pipx install pipenv
   ```

3. Run development environment (With Flask)

   ```
   pipenv run flask run
   ```

## Running in production mode

With *pipenv* installed:

```
pipenv run gunicorn
```


[1]: https://github.com/pypa/pipenv
[2]: https://pipxproject.github.io/pipx/
