# Changelog
All notable changes to Noruh Project project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Noruh](https://noruh.ilhasoft.mobi/).

## [1.0.34] - 2019-04-12
### Added
- Add quantity to on orders kitchen card
- change value intervals for accept payments(now the user can pay a bill for all_members including noruh_fee by app and by web)
- change forms to reset password
- improve notifications
- add method to reject a payment
- Add switch to enable or disable establishment(have a bug on animation)

### Fixed
- Fix bugs on dashboard chart and improve values on cards
- When accept a order, returns to a kitchen orders list pending

## [1.0.33] - 2019-04-10
### Added
- Improve values and payment methods on noruh web
- Add button to remove filter on orders list kitchen
- Add label showing that are filtering on orders list kitchen
- Active nav bar when filter on orders list kitchen

### Fixed
- Fix values on dashboard “ticket medio”
- Fix values that use % on establishment configurations

## [1.0.32] - 2019-04-09
### Added
- Add `.` on `Faturamento Total` dashboards
- Add more fields on `ranking de desempenho` dashboard
- Can alter Establishment Location
- Improve filter on orders list on kitchen
- Improve values to `ticket medio`, `faturamento` and `closed bills list`
- Improve layout on user logged
- Title added in categories and observations

### Fixed
- Switch for featured now it's work
- Bug card broken fixed
- Bug manager dashboard fixed

## [1.0.31] - 2019-04-08
### Added
- Add `CRUD` for Categories and Observations
- Improve Establishment forms
- Improve wirecard/moip forms for establishment
- Add sentry to server
- Improve title on forms when are Modals
- Change label on dashboard's graphic

## [1.0.30] - 2019-04-04
### Added
- Add notification when customer create a order with discount
- Add value for `offline_percentage` on establishment configurations
- Add `R$` on value on `Contas Pagas` screen
- Changed `Cobrar` to `Pago` on Screen about Offline payments
- Added filter on Screen kitchen


## [1.0.29] - 2019-04-03
### Added
- add count customers on dashboard(male, female, all_users and others)
- add offline payment reports
- add field to offline percentage on establishment taxes configuration forms

### Fixed
- fix bugs when count month
- change the name on ‘repasse offline’

## [1.0.28] - 2019-04-03
### Added
- Improve dashboard on all establishments
- add offline payment reports

### Fixed
- Fix a bug when create/accept offline payment, customer can't quit from bill
- Fix line on screen when accept a payment, now is a continuing line

## [1.0.27] - 2019-04-01
### Added
- Added layout for show when users haven't permissions to access the page

### Fixed
- Align table list on table zone cards

## [1.0.26] - 2019-03-29
### Added
- Add noruh_fee to payment, and create a field for noruh_fee on offline_payment
- Add credit card on ‘Contas Pagas’
- Add fields to credit_card on bill_payment endpoints

### Fixed
- The bug: Btn cancel is clickend and work equals a submit btn
- btn cancel receive a new type = reset, and works like a btn cancel now.
- Refactor api method to add a credit card
- Fix a bug on items more requested on manager dashboard
- Fix bug on dashboard ‘total of orders'

## [1.0.25] - 2019-03-27
### Added
- perspective for api documentation
- run pep8 and add comments to views for api

### Fixed
- Fix bugs in modals
    - establishment accounts (modals) [ok]
    - establishment tables and zones (modals) and edit_table_zone [ok]
    - establisment menu (modals) [ok],
    - establishment new user [ok]
    - establishment offer (modals) modal offer update and create [ok]
    establishment config (modals) [ok]

## [1.0.24] - 2019-03-25
### Added
- add colunms to 'contas pagas' and create a filter by month
- create disable establishment
- organize urls code
- run pep8 on urls
- comment exception and improve serializers code

### Fixed
- change filters on dashboard
- cannot create a menu_item without category
- improve location info on api list

## [1.0.23] - 2019-03-19
### Added
- Create validation for username, and email when create a employee
- Add a message when user haven’t a employee object, show that user havent permission for access the Noruh-Web
- Translate all forms
- Disable notification dropdown of starting on load

### Fixed
- Fix a bug when create a bill
- Fixing the responsiveness of kitchen orders list
- Fix padding
- Adjust the margin for cards

## [1.0.23] - 2019-03-19
### Added
- create views for accept requests and all requests
- Create a template with cards and buttons to requests lists to waiter

## [1.0.22] - 2019-03-19
### Added
- Add icon pencil on Employee cards
- Add modal and view for edit a Offer Range Value
- Now de Establishment can have more than one Manager

### Fixed
- Improve values on Employee cards
- Fix color from pencil when edit a events
- Correct a bug when create a order(list only bills from the current establishment)
- Fixed enconding the name from image files, now accept files with others enconding

## [1.0.21] - 2019-03-18
### Added
- Super admin can see offers about Establishment

### Fixed
- Improve Ticket Medio on dashboard

### Removed
- Remove observation from Bill

## [1.0.20] - 2019-03-15
### Added
- Added the notification in real time
- Add column status on Orders from Bill Table

### Fixed
- Change column to ‘cancelar’ for next ‘Status’ Column
- Improve screen for orders done, and create a table

### Removed
- Remove name ‘Contas em Aberto’ to super user and apply rules for nav bar when Super user use the dashboard

## [1.0.19] - 2019-03-15
### Added
- Added the notification in real time

### Fixed
- Fixed the error of the requests

## [1.0.18] - 2019-03-14
### Added
- Add modals to 'Excluir' button
- can create a menu item without observations as and add a button to cancel orders
- create a button for cancel order
- Add ‘Contas’ option on nav bar to super admin
- Add icon grey on tables and fix rules
- Add gender to Profile
- Set null for a category field on item when delete a Category

### Fixed
- correction in css for orders to stop breaking with less than 3 cards.
- Change Photos Icons, must be equal to Sympli
- Change icons about qr code, must be equal to Sympli
- Change icons about amenities, must be equal to Sympli
- Change button 'x', must be equal to Sympli
- Align promocode card
- Align events card
- Improve switches, some doesn't work
- Improve business rules about Taxes
-‌ ‘Pagar taxas do Moip’ must be a switch, must be only visible to SuperAdmin
- The button ‘Editar Couvert’ must be visible to Manager
- ‌‘Editar Taxas’ must be only visible to SuperAdmin
- change help text for preparation time and cd create a screen about bills paid
- Improve querys on dashhboard
- Fix a bug on categories nav bar when make a order
- Change calc to average ticket on establishment dashboard

### Removed
- Remove 'adicionar horário' and map to on 'Editar' Button
- Remove 'horários disponíveis' in schedules
- remove configuratios and views for Amenities and Cuisine Types,

## [1.0.17] - 2019-03-13
### Added
- Value consumed from bill member when create a payment on Front End Web
- add string begin of menu_items
- Add when create a evaluation answer to a modal
- Add table_form create modal
- Fix table on-off switch

### Fixed
- Fix values on Bill and BillMember List
- Improve methods from orders
- Improves names and standardize fonts from titles
- Run pep8 in some files
- Fix the extra configurations on off switch

### Removed
- Remove link for active/desactive table zone

## [1.0.16] - 2019-03-11
### Added
- Add delete icon for menu_item_list and change the edit button
- Add customized checkbox for menu_item_create and menu_item_update
- Add new image icon on forms to create and edit a menu item

### Fixed
- Fix the filter for menu and improve for both menu and orders
- Change the help texts on menu item forms
- Improve the template for creating a menu item
- Improve the template for editing a menu item

## [1.0.15] - 2019-03-08
### Added
- Add 'Pedidos' to the table header
- Add filtering options for menu_item_list_to_order
- Add lib django_widget_tweaks
- Add modal view for order_form
- Finish the post action for order-form    
- Change Rules when delete a evaluation, only super admin can delete a evaluation   
- Change value from establishment.payment_tax, now is like %5,49
- Add field Descrpition on MenuItem at Api

### Fixed
- Translating django default texts and improving employee_form
- Improve template for menu_item_list_to_order
- Fix the page title for employee form
- Filter now works by category
- Overflow on tablezone card - active scroll

### Removed
- Removing unused template
- Remove icon and establishment name from base

## [1.0.14] - 2019-03-08
### Added
- Add name from menu offer on endpoint when create a order
- Front-end in kitchen configurated but have a bug, the tags(observations) don't print.
- Card is loading when ok alert is clicked
- Add box to orders_from_bill object

### Fixed
- Fix filters on Orders List, now list all orders from establishment with status in preparing or pending
- Maintain bill value into the screen
- Adjust alignment and titles for orders_from_bill
- Adjust payment display for bill_members_card
- Fix the url for create full payment
- Fix the display for orders_from_bill modal

## [1.0.13] - 2019-03-07
### Added
- Adapt the view bill list for new layout
- Add delete modal for table_zone_list
- Add delete modal for evaluation view

### Fixed
- Fix the layout for bill list
- Refactor the function deleteAction and add the delete modal for employee_list

## [1.0.12] - 2019-03-01
### Added
- Change permission for endpoints `cuisine_list` and `establishment_detail`

### Fixed
- Fix bugs on Table List and Table Zone Cards
- Set id for profile when create a user
- Fix queryset to bill active on api, now is get user if is the same user instance
- Improve payment flow on web and resizing the modal for payment
- Fix the create payment modal, now it's working
- Remove titles from Dashboards on SuperAdmin view
- Clear `console_log` on JavaScript files
- Fix filters on order_list

## [1.0.11] - 2019-03-01
### Added
- Endpoint to verify if promocode is valid or enabled

### Fixed
- Fix bugs in graphics on dashboard, both for establishment and all establishments

## [1.0.10] - 2019-02-28
### Fixed
- Fixed callback links on establishment configurations

## [1.0.9] - 2019-02-27
### Added
- Send notification to waiters when create a new bill
- Complete structure organization in establishment/config, front-end in progress new generals css added

### Fixed
- Fix bugs in menu offer
- Fix pagination on menu item list
- Fix words on forms to menu item
- Fix models the option on_delete to Item related to MenuOffer

## [1.0.8] - 2019-02-26
### Added
- Screen for kitchen it's ready for implement cards with real time, including filters and flow

### Fixed
- Improve grapichs, now it's works

## [1.0.7] - 2019-02-26
### Added
- Improve screen about configurations
- Improve cards, now they are more rounded

### Fixed
- Fix bug when create a table_zone
- Fix a bug when create a table
- Fix little bugs on front end to responsive

## [1.0.7] - 2019-02-25
### Added
- Another Command for populate database
- Create two distinct approach to view Users
- Added pagination from evaluation list

### Fixed
- Fix menu item, now can update values from items
- fix preparation time for time field
- Fix the navigation bar flow for superdmin viewing establishments
- Standardizing Establishment view
- Fix bug for always list answer button

## [1.0.6] - 2019-02-25
### Added
- Dashboard for SuperUser
- Added `R$` to contas
- Added widget for filtring by month
- Added title to dashboard view
- Added filter by month
- Added the basic skeleton for the graph

### Fixed
- Fix dashboard for manager and added Graphics
- Fix table ordering
- Change switch for Open or Close Establishment

## [1.0.5] - 2019-02-22
### Added
- Add `id` for menu_offer
- Add screens with make payment

### Fixed
- Make login by email

## [1.0.4] - 2019-02-20
### Added
- Create filter for graphics on SuperAdmin dashboard
- Added payment_uuid on Payment endpoint and BillPayment Models
- Create a command `create_database_example`
- Define the form HTML manually for employee_form
- Add new code rendering form_employee
- Altered the bill list template and added a card template as well.
- Feature upsell complete
- Prepration time on api, now it's returning a integer with only minutes, now the complete Time Field
- View from QR Codes on configurations
- Screen on Bill Members on List Table to make a Payment
- Added table_orders template(Missing the view with the variables but should be a no-brainer to update. The navigation tab also needs to be updated with the view url)
- Added Tables and TableZone list(Missing the AJAX call in order to enable/disable the table.)

### Removed

### Fixed
- Improve values for SuperAdmin dashboard
- Consolidation value for orders
- Improve payment and populate new fields
- Fix a bug when bill member can leave a bill
- Fix a bug on screen orders list, and set the correct link to create a new order
- Fix a bug, the photo from most requested items doesn't load on establishment manager dashboard
- Fix a bug when super admin list details about establishment and doesn't show the correct name from establishment
- Fix a bug to calculate value total from a bill(taxe courvet + orders + taxe service)
- Correct the form on MenuItem with preparation time
- Fix a bug when list evaluations, doesn't list the answer from establishment
- Fix correct form on employee(its missing add table zone for waiter)

## [1.0.3] - 2019-02-14
### Added
- Developed on front end screen about evaluations from Establishment

### Removed

### Fixed
- Fix login web page, change label for pt-br(username and password)
- Adjusting the login page for a more responsive layout

## [1.0.2] - 2019-02-12
### Added
- Screen about Orders, on `orders_list.html`

### Fixed
- Fixed the logo_url error at template level
- Fixed the page layout

## [1.0.1] - 2019-02-11
### Added
- Endpoint to BillMember can cancel a request to join in a bill `(path: bill/join/cancel/)`
- database_example.json to help populate databases, for help developers(front end) to understand the code and the Project
- `logo_url` for establishment now is required
- The feature remember-me when user login on web, now is actived
- Templates on front end for login, forgot my password, reset password, and password reset done, now is implemented

### Removed

### Fixed
- Fix a bug, when close a bill with payment, the bill still accept new orders, now can't anymore, with a bill has `bill_payment`, the user can't make a order
- Fix menu search list, on Menu Item List template view
- Improves on `base.html` for implement the bar navigation to super admin when see establishment.

## [1.0.0] - 2019-02-08
### Added
- Validation for a user only can make a payment once on Payment Offline and Online on Endpoints.
- Create a validation for User can create a UserRating, only can create if have the variable `leave_at` not null.
- Improve offline payment
- Improve confirmation for offline payment on web view
- Added effect to element when select on horizontal navigation
- Started fix on establishment base to become more modularized
- Prepared screen configurations to receive more differents forms that will be
- Created subtemplates for screen configurations

### Removed
- Removed pagination from amenity list

### Fixed
- Validates created when create a credit card, some scenarios the flow broken
- Change path exit
- Update average spent and establishment count when User pay a bill
- When reset a password, correct link for reverse login
- Now superadmin can create events, tables, tablezone, menu itens for each establishment
- Added CSS for fix images on menu item screen
- Fix cancel button on modals at menu item screen
- Started refactor on code at modals for menu items screen, would generalize the flow to the different modalities
- Fix layout on users screen
- Fix layout on establishments screen
- Fix error `the establishment has no logo_url`  on template at screen configurations
