## Database Structure

### Tables Used

- Customer Table: Stores demographic and profile information of customers. This data is used for segmentation analysis, repeat customer analysis, CLV estimation, Identifying high value demographics.

- Cars Table: This is the master table for all the cars sold. This table is used for product performance analysis, brand/model profitability, segment demand trends.

- Sales Table: Transaction fact table containing all the sales. This is the core table for revenue/ profit and business analysis.

- Branches Table: Stores dealership branch details. This is used for branch table benchmarking, city-wise comparisons, operational efficiency view.

- Salespersons Table: Stores employee salesforce details. This table is used for performance ranking, incentive analysis, productivity benchmarking

- Inventory Table: Tracks stocks across branches. This table is used for stock aging, inventory turnover, overstock and understock detection.

- Financing Table: Tracks financing and loan packages. This is used for financing adoption analysis, bank preference comparison, loan preference trends.

- Servicing Table: Track post sale servicing. This table is used for retention analysis, after sales revenue, loyalty behavior.

- Marketing Campgain Table: Tracks lead generation campaigns. This table is used ROI calculation, Marketing effectiveness.

- Test Drive Table: Tracks showroom visits/ test drives. This table is used conversion funnel analysis, lead conversion optimization.

- Leads Table: The leads table captures every potential customer inquiry/prospect before they become buyers. This helps the management analyze: Lead Generation Volume, Campaign Effectiveness, Conversion funnel performance, Sales funnel leakage, Customer acquisition efficiency.

---

## Table Structure

### Customers Table

| Column | Description |
|----------|-------------|
| Customer_id | Unique customer identifier |
| Full_Name | Customer name |
| Gender | Gender of the customer |
| Age | Age of the customer |
| City | Residence city of the customer |
| Occupation | Job profile of customer |
| Annual_income | Income bracket of the customer |
| First_purchase_date | First ever purchase date |
## 

### Cars Table
| Column Name | Description |
|------------|-------------|
| Car_ID | Unique car identifier |
| Brand | Car manufacturer |
| Model | Car model |
| Segment | SUV, Sedan, Hatchback, Luxury |
| Fuel_Type | Petrol, Diesel, Electric |
| Transmission | Manual or Automatic |
| Showroom_Price | Listed showroom price |
| Cost_Price | Dealership acquisition cost |
##

### Sales Table

| Column Name | Description |
|------------|-------------|
| Sale_ID | Unique sales transaction ID |
| Customer_ID | Customer who purchased the vehicle |
| Car_ID | Vehicle sold |
| Salesperson_ID | Salesperson responsible for the sale |
| Branch_ID | Branch where the sale occurred |
| Sale_Date | Date of sale |
| Sale_Price | Final selling price |
| Discount_Given | Discount offered on the sale |
| Financing_ID | Financing package selected |
##

### Branches Table

| Column Name | Description |
|------------|-------------|
| Branch_ID | Unique branch identifier |
| Branch_Name | Name of the branch |
| City | Branch location |
| Manager_Name | Branch manager |
| Monthly_Operating_Cost | Monthly branch operating expenses |
##

### Salespersons Table

| Column Name | Description |
|------------|-------------|
| Salesperson_ID | Unique employee identifier |
| Salesperson_Name | Employee name |
| Joining_Date | Date of joining |
| Salary | Base salary |
| Branch_ID | Assigned branch |
##

### Inventory Table

| Column Name | Description |
|------------|-------------|
| Inventory_ID | Inventory record identifier |
| Car_ID | Vehicle identifier |
| Branch_ID | Branch holding the stock |
| Stock_Quantity | Available units |
| Arrival_Date | Date stock was received |

### Financing Table

| Column Name | Description |
|------------|-------------|
| Financing_ID | Loan package identifier |
| Bank_Name | Financing bank |
| Interest_Rate | Loan interest rate |
| Loan_Tenure_Months | Loan duration in months |
| EMI_Amount | Monthly EMI amount |
##

### Servicing Table

| Column Name | Description |
|------------|-------------|
| Service_ID | Service record identifier |
| Customer_ID | Vehicle owner |
| Car_ID | Serviced vehicle |
| Service_Date | Date of service |
| Service_Type | Repair or Maintenance |
##

### Marketing Campaign Table

| Column Name | Description |
|------------|-------------|
| Campaign_ID | Campaign identifier |
| Campaign_Name | Marketing initiative |
| Channel | Facebook, TV, Newspaper, etc. |
| Budget | Campaign spending |
##

### Test Drive Table

| Column Name | Description |
|------------|-------------|
| Drive_ID | Test drive identifier |
| Customer_ID | Prospect customer |
| Car_ID | Tested vehicle |
| Branch_ID | Branch location |
| Drive_Date | Test drive date |
| Converted_To_Sale | Yes / No indicator |
##

### Leads Table

| Column Name | Description |
|------------|-------------|
| Lead_ID | Unique lead identifier |
| Customer_ID | Associated prospect/customer |
| Campaign_ID | Marketing campaign source |
| Branch_ID | Branch handling the lead |
| Lead_Date | Date lead was generated |
| Lead_Source | Walk-in, Website, Facebook, Referral |
| Lead_Status | Open, Contacted, Qualified, Lost, Converted |
| Assigned_Salesperson_ID | Assigned salesperson |
| Expected_Budget | Prospect's expected budget |
| Interested_Car_Segment | SUV, Sedan, Hatchback, Luxury |
| Conversion_Date | Date lead converted into a sale |

