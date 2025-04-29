# GoComet Shipment Tracking and Error Resolution Guide

## About This Document

This document contains guidance on how to use the GoComet platform to track your shipments. Our customer support agents use this documentation to help you navigate the platform, but please note that **support agents cannot directly access your tracking data or perform tracking operations on your behalf**. All tracking functions must be performed by you through the platform interface.

## How to Rectify Shipment Marked as Invalid

### Common Error Reasons and Solutions

| Reason | Explanation | Next Actionable |
|--------|-------------|----------------|
| Invalid Tracking Number | The tracking number is invalid as the details are not available for the number on the carrier's website. | See detailed actions below |
| Tracking number does not match the carrier format | Every carrier has a set of tracking number formats used for tracking. This error is raised when your number doesn't match it. | Please check the tracking ID again |
| Tracking no. not found on mentioned shipping line website | The tracking ID is added with the wrong carrier. | Enter the right carrier |
| Need BL no. for the complete schedule of the shipment | BL number is required to know the full schedule of the tracking. | Please try to track the shipment via BL number as the carrier doesn't provide a complete schedule from the container number |
| Carrier is not found | The carrier name is not mentioned. | See detailed actions below |
| Your entered POL and POD not matched with carrier POL and POD | POL/POD entered for the tracking does not match with the carrier's data provided. | Please check whether the entered POL/POD is correct by visiting the platform |
| Dispatch Date error | The dispatch date entered is ahead of the Gate In date given by the carrier. | Entered factory dispatch date should be before the gate-in date (fetched from the carrier) |

### Detailed Error Resolution

#### Error: Invalid Tracking Number

**Reasons why shipment might be invalid currently:**

1. **The shipment you are trying to track is a future shipment**
   - Shipments which are yet to start or starting on a later date, may not be available on the carrier's database at the time of creation.
   - You can make your shipment a future shipment by adding a dispatch date or estimated departure.

   **Actionable:**
   - Adding Dispatch Date
   - Adding Estimated Departure Date

2. **Shipment is not in a valid format**
   - Please check if the tracking number is a container. If it is, make sure that it is in the format of 4 Alphabets + 7 Digits (e.g., MAEU1234567)
   - Please check if the tracking number belongs to the right carrier

   **Actionable:**
   - Edit shipment to the right tracking number

#### Error: Tracking number does not match the carrier format / Tracking no. not found on mentioned shipping line website

**Reasons:**
- Please check if the tracking number is a container. If it is, make sure that it is of the format of 4 Alphabets + 7 Digits (e.g., MAEU1234567)
- Every carrier has a certain prefix or owner code attached to the tracking number. For example, Maersk uses MAEU and MRKU as prefixes for tracking numbers.

**Actionable:**
- Edit tracking number

#### Error: Need BL no. for the complete schedule of the shipment

**Reason:**
- Certain shipping lines like EGLV (Evergreen), BLPL, etc. only show the latest event when searched with container numbers.
- In such cases, adding a BL/Booking number will help you get the full schedule of your shipment.

**Actionable:**
- Change Container number to BL Number

#### Error: Carrier is not found

**Reason:**
- This happens when the carrier is not mentioned or not found on the platform. In such cases:
  - Either the entered carrier is misspelled
  - Carrier is not supported on the platform

**Actionable:**
- You can check the availability of existing carriers by going through the bulk upload template
- You can email support@gocomet.com
- You can also request for the carrier if not present. All you need to provide are:
  - Requested carrier name
  - A recent BL number
  - A recent container number
  - The current source of tracking: Website/call/sms/email
  - Volume (Optional: Volume of containers you deal with monthly)

#### Error: Your entered POL and POD not matched with carrier POL and POD

**Reason:**
1. Port of loading or discharge entered is different from BL. In such cases, we alert the user.
   - Note: We don't track shipments until action is taken on them.
2. Ports have changed due to delays or traffic. In such cases, we alert the user.
   - Note: We don't track shipments until action is taken on them.

**Actionable:**
- Autofix or change ports

#### Error: Factory Dispatch date error

**Reason:**
1. Users may be trying to track the next leg of the containers but the data is only present of the previous leg.
   - Our system provides a buffer of +5 days considering human error as dispatch date is not readily available.
   - We will mark the shipment yet to start if old leg data is available in the carrier's database till the dispatch date you have entered.
2. User might have entered a wrong dispatch date

**Actionable:**
- Add dispatch date before gate in date

### Step-by-Step Action Guides

#### Actionable for tracking ID format not matching:

1. Login to the platform and search for the particular tracking on the platform. Click on "More" option to the right of the tracking
2. Click on "Edit" option to make changes to the shipment
3. A modal will pop up. Now edit the BL number as per the correct tracking number and click on the "Submit" button. The shipment will be added for tracking successfully

#### Actionable for invalid tracking:

1. Login to the platform and search for the particular tracking on the platform. Click on "More" option to the right of the tracking
2. Click on "Edit" option to make changes to the shipment
3. A modal will pop up. Now edit the BL number to correct BL or a new BL number depending upon your use case and click on the "Submit" button. The shipment will be added for tracking successfully

#### Actionable for tracking no. not found on mentioned shipping line website:

1. Login to the platform and search for the particular tracking on the platform. Click on "More" option to the right of the tracking
2. Click on "Edit" option to make changes to the shipment
3. A modal will pop up. Now edit the carrier name as per the correct one and click on the "Submit" button. The shipment will be added for tracking successfully

#### Actionable for need BL no. for the complete schedule of the shipment:

1. Login to the platform and search for the particular tracking on the platform. Click on "More" option to the right of the tracking
2. Click on "Edit" option to make changes to the shipment
3. A modal will pop up. Now edit the carrier name as per the correct one and click on the "Submit" button. The shipment will be added for tracking successfully

#### Actionable for carrier not found:

1. Login to the platform and search for the tracking on the platform. Click on "More" option to the right of the tracking
2. Click on "Edit" option to make changes to the shipment
3. A modal will pop up. Now edit the carrier name as per the correct one and click on the "Submit" button. The shipment will be added for tracking successfully

#### Actionable for carrier name not found:

1. Login to the platform and go to "tracking bulk upload" appearing on the top right of the platform
2. Click on "Download template" option to download bulk upload sheet
3. In the spreadsheet, go to Shipping Line helper Sheet to see if the carrier you are trying to add is integrated with GoComet
   - Search for the carrier name in this sheet to see if you have typed in the exact name (name should match the B column of the sheet)
   - If the carrier is still not found, contact support@gocomet.com for further assistance

#### Dispatch date error & adding dispatch date:

1. Login to the platform and search for the tracking on the platform. Click on "More" option to the right of the tracking
2. Click on "Edit" option to make changes to the shipment
3. A modal will pop up. Now edit the dispatch date to be greater than gate in date
   - Note: Dispatch date is the date when the goods leave your factory, it should ideally be greater than Gate In (First milestone that appears in table view)
4. If the problem still persists you can contact support@gocomet.com for assistance or click on "report error" on the tracking

#### POL POD Mismatch:

1. Login to the platform and go to action required tab present on the right side
2. Click on the tracking to take the necessary action
3. If the problem still persists you can contact support@gocomet.com for assistance or click on "report error" on the tracking

## How to Add a Shipment for Tracking to the Platform
[Link to solution article](https://gocomet.freshdesk.com/a/solutions/articles/43000626200?portalId=43000006477)

### Step 1
Click on the "Add Shipment" button on the top left side of the screen.

### Step 2
Fill in the details in the pop-up box:

- **Group** - If a user is present in multiple groups, they need to select a group from which the shipment needs to be uploaded
- **Mode** - Ocean or Air (Mandatory)
- **Shipping line** – Name of the Shipping Company carrying the container (Mandatory)
- **MBL/Container Number** - Shipment is tracked using this number (Mandatory)

[**Note: If you are adding the ocean shipment using the HBL number, kindly add the name of the Freight Forwarder/NVOCC and not the shipping line**]

- **Consignee** - The receiver of the shipment. This stakeholder will be notified about the Arrival or Delay of the shipment
- **Reference number** - A number given to the container that can be internal to the company
- **Factory Dispatch date** - The date on which the shipment left the factory
- **Origin** - Starting Port
- **Destination** - Final Port

Enter the details and click on the "Submit" button.

## How to Add Multiple Shipments for Tracking at Once
[Link to solution article](https://gocomet.freshdesk.com/a/solutions/articles/43000626206?portalId=43000006477)

### Step 1
To add shipments in bulk click on the "Bulk Upload" button on the screen.

### Step 2
A new dialogue box will pop up.

### Step 3
Click on the "Download template" button to download the excel file. Once the template is downloaded, open the template and fill in the data as per your requirement.
**Note - Always download fresh bulk upload Excel template while using the "Tracking Bulk Upload".**

### Step 4
Fill the Excel template:

- **Column A --> Mode (Mandatory)**: Select the type of mode for the shipment from the dropdown (Ocean or Air)
- **Column B --> Reference no. (Optional)**: Mention the reference name/no. for the shipment
- **Column C --> Tracking Number (BL, Booking or Container Number) (Mandatory)**: Mention the tracking no. by the shipment can be tracked on the shipping line website
- **Column D --> Carrier (Mandatory)**: Mention the shipping line/airline name of the shipment by which it will be transported

[**Note: If you are adding the ocean shipment using the HBL number, kindly add the name of the Freight Forwarder/NVOCC and not the shipping line**]

- **Column E --> Container Numbers (Optional)**: Mention the container numbers
- **Column F --> Factory Dispatch Date (Optional)**: The dispatch date of the shipment can be mentioned
- **Column G --> POL**: Name of the Port of Loading
- **Column H --> POD**: Name of the Port of Destination
- **Column I --> Star Marked/Priority**
- **Column J --> Team unique code (optional)**: If you have multiple teams for multiple locations, you can update the unique code in this column which will provide only the relevant data to the respective teams
- **Column K --> Customer unique code (optional)**: If you have multiple consignees companies for multiple locations, you can update the code in this column which will display only their shipments on their dashboard
- **Column L --> Carrier Code**: Once you mention the carrier name, the carrier code will be automatically updated. **Note: Do not make any changes in the cells of column L as it is a formulated column used for detecting if the user has added the correct carrier name in column D**
- **Column M --> Share With**: Team code of the team with which a particular shipment is supposed to be shared
- **Column N --> Vessel Name**: For shipments where the carrier requires vessel name, the field will be highlighted and needs to be filled

### Step 5
Once you update the mandatory data in the excel sheet (Column A, C, and D), save the file on your PC and upload the same by clicking on the "Click to upload" button to upload the file.

### Step 6
Once you upload the file, the system will check for any errors present in the file. If there is any error, the system will help you identify the errors. Once the errors are identified, you can rectify those errors and re-upload the file.

### Step 7
Once the file is completely error-free, click on the "Import data" button. You can see all the shipments from the Excel sheet uploaded on the platform.

## How to Update Multiple Shipments at Once
[Link to solution article](https://gocomet.freshdesk.com/a/solutions/articles/43000669665?portalId=43000006477)

### Step 1
To update shipments in bulk click on the "Edit Shipments" button on the screen.

### Step 2
A new dialogue box will pop up.

### Step 3
Click on the "Download template" button to download the excel file. Once the template is downloaded, open the template and fill in the data as per your requirement.
**Note - Always download fresh bulk upload Excel template while using the "Tracking Bulk Upload".**

### Step 4
You can update the following fields for your trackings:

- **Reference no. (Optional)**: Mention the reference name/no. for the shipment
- **Carrier (Mandatory)**: Mention the shipping line/airline name of the shipment by which it will be transported

[**Note: If you are adding the ocean shipment using the HBL number, kindly add the name of the Freight Forwarder/NVOCC and not the shipping line**]

- **Factory Dispatch Date (Optional)**: The dispatch date of the shipment can be mentioned
- **POL**: Name of the Port of Loading
- **POD**: Name of the Port of Destination
- **Team unique code (optional)**: If you have multiple teams for multiple locations, you can update the unique code in this column which will provide only the relevant data to the respective teams
- **Customer unique code (optional)**: If you have multiple consignees companies for multiple locations, you can update the code in this column which will display only their shipments on their dashboard
- **Carrier Code**: Once you mention the carrier name, the carrier code will be automatically updated
- **Share with**: You can also share your trackings with multiple groups using bulk update

**Note:**
1. You can also archive shipments in bulk [Archived column]. If marked as "TRUE", shipments will be archived. If marked as "FALSE", shipments can be restored.
2. You can also update other additional columns which you have set up for your account.

### Step 5
Once you update the data in the sheet, save the file on your PC and upload the same by clicking on the "Click to upload" button to upload the file.

### Step 6
Once you upload the file, the system will check for any errors present in the file. If there is any error, the system will help you identify the errors. Once the errors are identified, you can rectify those errors and re-upload the file.

### Step 7
Once the file is completely error-free, click on the "Import data" button. You can see all the shipments from the Excel sheet updated on the platform.

## How to Share an Added Shipment with Other Teams of Your Company
[Link to solution article](https://gocomet.freshdesk.com/a/solutions/articles/43000646084?portalId=43000006477)

### If the shipment is already added to the platform
1. Click on the "more" button at the extreme right end of the shipment. Later click on the "Edit" button.
2. The system will display the Edit Shipment form consisting details of the shipment. In the edit form, there is a field "Share with", where the user can add multiple teams by writing the name of the team in the box.
3. Once the name of the teams are selected to whom the shipment needs to be shared, click on the button "Submit".

### While adding a shipment to the platform
Click on the button "Add Shipment". An Add Shipment form will open up. You can also find a field of "Share with" in the form. You can simply add the teams and the shipment will be directly shared with the other team once added to the platform.

## How to Analyze/Edit/Bookmark/Archive Shipment
[Link to solution article](https://gocomet.freshdesk.com/a/solutions/articles/43000626219?portalId=43000006477)

### Container display on dashboard
- Reference number is shown on the left top corner
- POL and POD are shown with the country flag
- Abbreviated carrier name is shown
- Arrival date shows ETA
- The status is shown on the extreme side

### Actions available via "More" button
- **Edit** – Edit helps in changing Consignee, Reference Number, Factory Dispatch date of that particular shipment
- **Bookmark** - Bookmark multiple shipments that you can view on priority
- **Archive** - In order to archive any shipment

## Understanding the Details of the Shipment Added for Tracking
[Link to solution article](https://gocomet.freshdesk.com/a/solutions/articles/43000626222?portalId=43000006477)

### Analyzing the shipment through "Table View"
1. Click on any shipment to view the complete details
2. View the current status of your shipment. In order to see the table view of your shipment, click on "Table View"
3. Understand the table elements:
   - **Event**: A major activity that takes place in shipment movement. Some of the milestones which are involved in the shipment are:
     - The arrival of Transport at Origin
     - Goods Loaded in Transport
     - Departure from Origin
     - Trans-Shipment Arrival
     - Trans-Shipment Departure
     - Arrival at Destination
     - Goods Unloaded at Destination
   - **Location**: The place at which the activity takes place
   - **Original Plan**: The date on which the event was supposed to take place
   - **Current Plan**: The date on which the event is now supposed to take place
   - **Actual date**: The date on which the event actually takes place
   - **Mode**: The mode of transport for moving the shipment
4. The progress bar is the green tick mark on the left-hand side shows the events along with the status, location, original plan date & time, current plan date & time, actual date, and mode. When each event is completed at a location, it is shown in a green tick mark.

### Analyzing the shipment through "Map View"
1. Click on any shipment to view the complete details
2. View the current status of your shipment. In order to see the map view of your shipment, click on "Map View"
3. The map view shows the container movement on the map with locations
4. Reference No, Tracking number, POL, POD, Carrier, Consignee, Shipment Count and Estimated arrival date is shown on the top portion of the tracking screen. Shipment count is the number of containers in that shipment
5. The progress bar is the green tick marks on the right hand side shows the events along with the status, location, planned date and actual date. When each event is completed at a location, it is shown in green tick mark along with its planned and actual date

## How to Upload Detention and Demurrage Data on the Platform
[Link to solution article](https://gocomet.freshdesk.com/a/solutions/articles/43000677094?portalId=43000006477)

### Method 1: Adding rates for each shipment
1. Click on "Add Shipment". A dialog box will appear for you to add the tracking details. Add the required details.
   - *Note: Detention and Demurrage fields will remain greyed out unless you add the port of loading and destination.*
2. Add the port of loading and destination, then click on "Add Detention & Demurrage Details". Enter the relevant information in the dialog box that pops up, and then click on save once done.
3. Click on Submit in the Add Shipment dialog box and the shipment will successfully be added with the Detention & Demurrage details.

### Method 2: Adding Contracted/Periodical Detention and Demurrage data in one go
Bulk upload of Detention and Demurrage comes in handy when you have multiple shipments to be uploaded and the Detention and Demurrage rates are contracted for a certain period. You simply need to create the rates master on the platform once with the contracted start and end dates and it will be applicable for all the shipments added.

1. Go to the section in the top-right corner of the page on the navigation bar
2. Select the relevant team from the Select your team dropdown
3. Go to the Preferences section and then to Tracking > Detention and Demurrage Charges
4. Download the excel file available from the link given
5. Fill up the necessary details for all the contracted Detention and Demurrage details in the excel sheet
   - *Note: There are 2 different sheets in the same excel sheet for Detention and Demurrage specifically*
   - Also, helper sheets for the Shipping line, seaports, and currency are available
6. Upload the completed file back to the platform

The platform will verify the sheet for any input errors and once the file is verified, you can click on import data on the platform. If there are any errors highlighted by the system, you can make the necessary changes and reupload the file.

***Please note that Demurrage & Detention validity will be checked against the date on which the shipment was added for tracking on the GoComet platform.***

## Understanding Carrier Ratings for GoTrack [P1, P2, P3]
[Link to solution article](https://gocomet.freshdesk.com/a/solutions/articles/43000631963?portalId=43000006477)

GoComet's support ratings define the service level parameters for different carriers while tracking shipments on our platform (GoTrack: Enterprise Shipment Tracking solution & Container tracking free tool). These ratings are standard across all the supported modes - Air, Ocean, and Courier, Road.

Carrier support ratings are defined based on the type of Integration between GoComet & the carrier (API, EDI, Legacy platform/database integrations).

**Note**: If there is a discrepancy from carrier's data, GoComet resends the request to verify data, back to the carrier. Hence in a very few cases, you can expect the time for updation may take 12-24 hours regardless of the rating.

### Types:

1. **P1 Rating: Highest | Trusted by GoComet**
   - Marked with a P1 support rating are trusted carriers that are integrated directly for tracking updates with the GoComet Platform via API/EDI integrations
   - These carriers allow for instantaneous results in most cases providing the quickest updates
   - **Update response time**: Fastest | Typically: 1-2 minutes (In some cases: 3-6 hours), May take 12 hours if the data is not accurate from carrier

2. **P2 Rating: High | Supported by GoComet**
   - Marked with a P2 support rating are supported carriers that are integrated directly with the carrier's system for tracking updates via Legacy platform integrations
   - These integrations are unlike the state-of-the-art API/EDI integrations and provide much slower response times
   - As a result of which the total data refresh cycles are limited to 1-2 refreshes per day
   - **Update response time**: Typically: 12-24 hours

3. **P3 Rating: Medium | Smart Algorithm**
   - Carriers with a P3 rating don't have a Database or API GoComet could integrate with
   - These carriers are tracked using GoComet's ML Algorithm which identifies the ocean carriers dealing with the shipments
   - **Update response time**: Typically: 24-48 hours. In some cases, for trackings which have not started yet, data may take 4-5 days to get updated

4. **Not Supported Carriers**
   - Marked as "Not supported" are the carriers which do not support direct integration either due to poor/no IT architecture to support shipment tracking or strict no data-sharing policies (these carriers typically allow shippers to track shipments with a secure login ID)
   - Carriers that do not qualify with the minimum levels of data standards as per our policy after the evaluation period is also marked as "Not Supported"