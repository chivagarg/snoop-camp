* See ```https://github.com/chivagarg/snoop-camp/blob/main/campground_ids.py``` for list of campgrounds being snooped
* Instructions to update lambda function from local
* https://docs.aws.amazon.com/lambda/latest/dg/python-package.html
* To install a new dependency ```pip install --target ./package requests```
* ```cd package``` followed by ```zip -r ../my-deployment-package.zip .``` to package the new dep
* Then add the lambda_fuction.py file to the root of the zip ```cd ..``` followed by ```zip my-deployment-package.zip lambda_function.py README.md```
* Finally upload to AWS lambda ``` aws lambda update-function-code --function-name campsiteSnooper --zip-file fileb://my-deployment-package.zip```
* Project inspired from https://github.com/banool/recreation-gov-campsite-checker/blob/f3b589ada2c326196e933f80843111ce2a0b7c33/camping.py
* Project inspired from https://github.com/CunningDJ/RecreationGovAvailability/blob/master/recreationGovAvailability.js
* GET camground specific info https://www.recreation.gov/api/camps/campgrounds/232465 https://jsonformatter.org/json-pretty-print/ffb021
* GET campsite info https://www.recreation.gov/api/camps/campsites/2900 https://jsonformatter.org/json-pretty-print/048087
* Get availability of campsites for a campground https://www.recreation.gov/api/camps/availability/campground/232487/month?start_date=2020-08-01T00%3A00%3A00.000Z https://jsonformatter.org/json-pretty-print/8343cb
