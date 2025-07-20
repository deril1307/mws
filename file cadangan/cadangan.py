# def load_data():
#     if os.path.exists(DATA_FILE):
#         with open(DATA_FILE, 'r') as f:
#             return json.load(f)
#     return get_default_data()

# def save_data(data):
#     with open(DATA_FILE, 'w') as f:
#         json.dump(data, f, indent=2)

# def get_default_data():
#     return {
#         'parts': {
#             'AOA-001': {
#                 'partNumber': 'AOA-001',
#                 'serialNumber': 'SN123456',
#                 'tittle': 'Angle of Attack Indicator',
#                 'customer': 'Garuda Indonesia',
#                 'acType': 'CN235',
#                 'wbsNo': 'A/S90-025CN235-90-99-99',
#                 'worksheetNo': 'IN-108',
#                 'iwoNo': 'Z501-00001',
#                 'shopArea': 'IN',
#                 'revision': '1',
#                 'status': 'in_progress',
#                 'currentStep': 3,
#                 'assignedTo': '002',
#                 'startDate': '2024-01-15',
#                 'finishDate': '',
#                 'targetDate': '2024-01-25',
#                 'preparedBy': '',
#                 'preparedDate': '',
#                 'approvedBy': '',
#                 'approvedDate': '',
#                 'verifiedBy': '',
#                 'verifiedDate': '',
#                 'steps': [
#                     {
#                         'no': 1,
#                         'description': 'Incoming Record\nA. Check PN and SN to be according with MWS then record actual\nPN: ........................ SN: ............................\nB. Check document attachment needed are completed.\nC. Visual inspection for completed.\nRecord the part not completely if any\nDESCRIPTION    PN    SN    QTY',
#                         'status': 'completed',
#                         'completedBy': '002',
#                         'completedDate': '2024-01-15',
#                         'man': 'A',
#                         'hours': '',
#                         'tech': '',
#                         'insp': ''
#                     },
#                     {
#                         'no': 2,
#                         'description': 'Functional Test\nDo a Functional Test procedures ref. CMM,\nChapter 34-12-24, page 5.',
#                         'status': 'completed',
#                         'completedBy': '002',
#                         'completedDate': '2024-01-16',
#                         'man': 'A',
#                         'hours': '',
#                         'tech': '',
#                         'insp': ''
#                     },
#                     {
#                         'no': 3,
#                         'description': 'Fault Isolation\nDo a Fault Isolation procedures ref. CMM,\nChapter 34-12-24, page 5.',
#                         'status': 'in_progress',
#                         'completedBy': '',
#                         'completedDate': '',
#                         'man': 'A',
#                         'hours': '',
#                         'tech': '',
#                         'insp': ''
#                     },
#                     {
#                         'no': 4,
#                         'description': 'Disassembly\nDo a Disassembly procedures ref. CMM,\nChapter 34-12-24, page 13.',
#                         'status': 'pending',
#                         'completedBy': '',
#                         'completedDate': '',
#                         'man': 'A',
#                         'hours': 'U1',
#                         'tech': 'U1',
#                         'insp': 'U2'
#                     },
#                     {
#                         'no': 5,
#                         'description': 'Cleaning\nDo a Cleaning procedures ref. CMM,\nChapter 34-12-24, page 16.',
#                         'status': 'pending',
#                         'completedBy': '',
#                         'completedDate': '',
#                         'man': 'A',
#                         'hours': '',
#                         'tech': '',
#                         'insp': ''
#                     },
#                     {
#                         'no': 6,
#                         'description': 'Check\nDo a Check procedures ref. CMM,\nChapter 34-12-24, page 16.',
#                         'status': 'pending',
#                         'completedBy': '',
#                         'completedDate': '',
#                         'man': 'A',
#                         'hours': '',
#                         'tech': '',
#                         'insp': ''
#                     },
#                     {
#                         'no': 7,
#                         'description': 'Assembly\nDo a Assembly procedures ref. CMM,\nChapter 34-12-24, page 17.',
#                         'status': 'pending',
#                         'completedBy': '',
#                         'completedDate': '',
#                         'man': 'A',
#                         'hours': '',
#                         'tech': '',
#                         'insp': ''
#                     },
#                     {
#                         'no': 8,
#                         'description': 'Functional Test\nDo a Functional Test procedures ref. CMM,\nChapter 34-12-24, page 5.',
#                         'status': 'pending',
#                         'completedBy': '',
#                         'completedDate': '',
#                         'man': '',
#                         'hours': '',
#                         'tech': '',
#                         'insp': ''
#                     },
#                     {
#                         'no': 9,
#                         'description': 'FOD Control\nA. Personnel who carry out the component are wearing the FOD bag and should not wear attributes indicated to be FOD.\nB. Ensure the component being maintained are free from FOD, dust, and oil spill.\nC. Cleaning up the documents, materials, standard parts, or consumable parts and send them to the proper place.',
#                         'status': 'pending',
#                         'completedBy': '',
#                         'completedDate': '',
#                         'man': 'A',
#                         'hours': 'U1',
#                         'tech': 'U1',
#                         'insp': 'U2'
#                     },
#                     {
#                         'no': 10,
#                         'description': 'Final Inspection\nA. Check PN and SN of Angle Of Attack Indicator to be according with MWS.\nB. Check actual test Angle Of Attack Indicator for functional test and good external condition.\nC. Check operating to completed and properly stamped.\nD. Produce Serviceable Tag Release external Angle Of Attack Indicator.',
#                         'status': 'pending',
#                         'completedBy': '',
#                         'completedDate': '',
#                         'man': 'A',
#                         'hours': '',
#                         'tech': '',
#                         'insp': ''
#                     }
#                 ]
#             }
#         }
#     }
