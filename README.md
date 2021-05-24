# Secure Programming - Course project: Metadata Editor

## Project authors
- Joona Jokivuori joonaeemil.jokivuori@tuni.fi

## Quickstart
The required modules can beisntalled with when inside the app folder
```python -m pip install -r requirements.txt``` 

The project can be started using the start.bat script (for windows) or the start.sh script (for Unix). The scripts should open the url automatically, if not, see the url below.

If the scripts do not work, the Flask app can be run with the command
```flask run```
however, the variables FLASK_APP and FLASK_RUN_PORT need to be set to
flask_simple.py and 50000 respectively.

The application can then be accessed from the url:
```http://localhost:50000```

## Application usage
The application is a tool that allows editing and creating metadata files in the yaml format.
- uses a schema.yaml file to dynamically generate the fields in webpage
- validates and sanitizes the inputs based on the schema rules
- generates a metadata.yaml into to the output directory with the inputs
- for editing an existing file, it should be uploaded to the reference file

### Frameworks used ###
- Python [main language]
- Flask framework [for the webapp]
- Jinja2 [for templating]
- werkzeug [for secure filenames]
- jsonschema [for validating and sanitizing]

## Secure programming
The flask Secret Key is generated randomly using the secrets module's hex token function. This way the Flask secret key cannot be predicted, and used for malicious intents

Jsonschema is used to sanitize and validate the input fields. Valiation happens by the schema rules.
In the case of a faield validation, the yaml file is still generated but an error message is shown on the screen. The details of the failed validation can be seen in the CMD or terminal where the flask app is running.
Input fields are always sanitized, so there is are no warnings for such cases.

File upload happens securely, as the Flask Upload utilizes werkzeug secure filename to send a safe file name back to the app. Additionally, the browsers have a built-in security feature where the uploaded file path is not sent to the server.

## Testing
Due to the simple nature of the 'small' app, (the app has very simple features) I found no big reason to spend a lot of extra time writing automated test cases.

Input validation was tested with a few different schema rules to make sure that it works correctly in all cases. The easiest to test was the datetime rule, where the format needs to match _exactly_ the expected format.
In other cases, tested that the valiation works for enum rules (where the aollowed inputs are from a given list). Since the app generates a selector list when using an enum rule, a normal user will only choose a value that is from the list (which is allowed). The validation for this case was tested by using inspect element to change the value to a non-allowed-value. The validation successfuly showed an error.

Input sanitation was tested with a few different _malicious_ inputs. HTML alert scripts where tested with many different formats. Also, different request methods were tested, PUT, GET, DELETE, PATCH, all of them do not trigger any functions, as the backend only allows POST

Safe file upload is harder to test, as the browser has security features that do not allow for so much modification. But using a 3rd party application like Postman, it is possible to attempt to send a harmful file name to the backend using a POST request with the _harmful_ filename in the formdata.