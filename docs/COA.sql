-- =====================================================
-- Level 1 (UUID 和 coa_code 相似)
-- =====================================================
INSERT INTO too_acc.coa (id, ten_id, coa_code, coa_name, coa_level, normal_balance, is_posting, is_readonly, coa_status, description) VALUES 
('10001000-1000-1000-1000-100010001000', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '1000', 'Assets', 1, 'Debit', false, true, 'Active', 'Asset account'),
('20002000-2000-2000-2000-200020002000', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '2000', 'Liabilities', 1, 'Credit', false, true, 'Active', 'Liability account'),
('30003000-3000-3000-3000-300030003000', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '3000', 'Equity', 1, 'Credit', false, true, 'Active', 'Equity account'),
('40004000-4000-4000-4000-400040004000', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '4000', 'Revenue', 1, 'Credit', false, true, 'Active', 'Revenue account'),
('50005000-5000-5000-5000-500050005000', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '5000', 'Expenses', 1, 'Debit', false, true, 'Active', 'Expense account');

-- =====================================================
-- Level 2
-- =====================================================
INSERT INTO too_acc.coa (id, ten_id, parent_id, coa_code, coa_name, coa_level, normal_balance, is_posting, is_readonly, coa_status, description) VALUES 
('11001100-1100-1100-1100-110011001100', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '10001000-1000-1000-1000-100010001000', '1100', 'Current Assets', 2, 'Debit', false, false, 'Active', '流动资产'),
('12001200-1200-1200-1200-120012001200', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '10001000-1000-1000-1000-100010001000', '1200', 'Fixed Assets', 2, 'Debit', false, false, 'Active', '固定资产'),
('21002100-2100-2100-2100-210021002100', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '20002000-2000-2000-2000-200020002000', '2100', 'Current Liabilities', 2, 'Credit', false, false, 'Active', '流动负债'),
('22002200-2200-2200-2200-220022002200', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '20002000-2000-2000-2000-200020002000', '2200', 'Long Term Liabilities', 2, 'Credit', false, false, 'Active', '长期负债'),
('31003100-3100-3100-3100-310031003100', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '30003000-3000-3000-3000-300030003000', '3100', 'Owner Equity', 2, 'Credit', false, false, 'Active', '所有者权益'),
('41004100-4100-4100-4100-410041004100', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '40004000-4000-4000-4000-400040004000', '4100', 'Operating Revenue', 2, 'Credit', false, false, 'Active', '营业收入'),
('51005100-5100-5100-5100-510051005100', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '50005000-5000-5000-5000-500050005000', '5100', 'Operating Expenses', 2, 'Debit', false, false, 'Active', '营业费用');

-- =====================================================
-- Level 3
-- =====================================================
INSERT INTO too_acc.coa (id, ten_id, parent_id, coa_code, coa_name, coa_level, normal_balance, is_posting, is_readonly, coa_status, description) VALUES 
('11101110-1110-1110-1110-111011101110', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '11001100-1100-1100-1100-110011001100', '1110', 'Cash', 3, 'Debit', false, false, 'Active', '现金'),
('11201120-1120-1120-1120-112011201120', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '11001100-1100-1100-1100-110011001100', '1120', 'Accounts Receivable', 3, 'Debit', false, false, 'Active', '应收账款'),
('11301130-1130-1130-1130-113011301130', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '11001100-1100-1100-1100-110011001100', '1130', 'GST/HST Receivable', 3, 'Debit', false, false, 'Active', 'GST/HST应收'),
('12101210-1210-1210-1210-121012101210', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '12001200-1200-1200-1200-120012001200', '1210', 'Property Plant Equipment', 3, 'Debit', false, false, 'Active', '固定资产'),
('21102110-2110-2110-2110-211021102110', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '21002100-2100-2100-2100-210021002100', '2110', 'Accounts Payable', 3, 'Credit', false, false, 'Active', '应付账款'),
('21202120-2120-2120-2120-212021202120', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '21002100-2100-2100-2100-210021002100', '2120', 'GST/HST Payable', 3, 'Credit', false, false, 'Active', 'GST/HST应付'),
('21302130-2130-2130-2130-213021302130', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '21002100-2100-2100-2100-210021002100', '2130', 'Payroll Liabilities', 3, 'Credit', false, false, 'Active', '工资负债'),
('22102210-2210-2210-2210-221022102210', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '22002200-2200-2200-2200-220022002200', '2210', 'Bank Loans', 3, 'Credit', false, false, 'Active', '银行贷款'),
('31103110-3110-3110-3110-311031103110', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '31003100-3100-3100-3100-310031003100', '3110', 'Owner Contributions', 3, 'Credit', false, false, 'Active', '所有者投入'),
('31203120-3120-3120-3120-312031203120', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '31003100-3100-3100-3100-310031003100', '3120', 'Owner Draws', 3, 'Debit', false, false, 'Active', '所有者提款'),
('31303130-3130-3130-3130-313031303130', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '31003100-3100-3100-3100-310031003100', '3130', 'Retained Earnings', 3, 'Credit', false, false, 'Active', '留存收益'),
('41104110-4110-4110-4110-411041104110', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '41004100-4100-4100-4100-410041004100', '4110', 'Business Income', 3, 'Credit', false, false, 'Active', '营业收入'),
('41204120-4120-4120-4120-412041204120', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '41004100-4100-4100-4100-410041004100', '4120', 'Professional Fees Revenue', 3, 'Credit', false, false, 'Active', '专业服务收入'),
('51105110-5110-5110-5110-511051105110', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '51005100-5100-5100-5100-510051005100', '5110', 'Advertising', 3, 'Debit', false, false, 'Active', '广告费'),
('51205120-5120-5120-5120-512051205120', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '51005100-5100-5100-5100-510051005100', '5120', 'Meals and Entertainment', 3, 'Debit', false, false, 'Active', '餐饮娱乐'),
('51305130-5130-5130-5130-513051305130', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '51005100-5100-5100-5100-510051005100', '5130', 'Insurance', 3, 'Debit', false, false, 'Active', '保险费'),
('51405140-5140-5140-5140-514051405140', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '51005100-5100-5100-5100-510051005100', '5140', 'Rent', 3, 'Debit', false, false, 'Active', '租金'),
('51505150-5150-5150-5150-515051505150', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '51005100-5100-5100-5100-510051005100', '5150', 'Salaries and Benefits', 3, 'Debit', false, false, 'Active', '工资福利');

-- =====================================================
-- Level 4 (每个 Level 3 下面补一个叶子科目)
-- =====================================================
INSERT INTO too_acc.coa (id, ten_id, parent_id, coa_code, coa_name, coa_level, normal_balance, is_posting, is_readonly, coa_status, description) VALUES 
-- Cash 下面的叶子
('11111111-1111-1111-1111-111111111111', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '11101110-1110-1110-1110-111011101110', '1111', 'Bank Account', 4, 'Debit', true, false, 'Active', '银行存款'),
('11111112-1112-1112-1112-111211121112', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '11101110-1110-1110-1110-111011101110', '1112', 'Savings Account', 4, 'Debit', true, false, 'Active', '储蓄账户'),
('11111113-1113-1113-1113-111311131113', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '11101110-1110-1110-1110-111011101110', '1113', 'Petty Cash', 4, 'Debit', true, false, 'Active', '备用金'),

-- Accounts Receivable 下面的叶子
('11201121-1121-1121-1121-112111211121', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '11201120-1120-1120-1120-112011201120', '1121', 'Trade Receivable', 4, 'Debit', true, false, 'Active', '应收账款'),

-- GST/HST Receivable 下面的叶子
('11301131-1131-1131-1131-113111311131', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '11301130-1130-1130-1130-113011301130', '1131', 'GST/HST Receivable', 4, 'Debit', true, false, 'Active', 'GST/HST应收'),

-- Property Plant Equipment 下面的叶子
('12101211-1211-1211-1211-121112111211', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '12101210-1210-1210-1210-121012101210', '1211', 'Office Equipment', 4, 'Debit', true, false, 'Active', '办公设备'),

-- Accounts Payable 下面的叶子
('21102111-2111-2111-2111-211121112111', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '21102110-2110-2110-2110-211021102110', '2111', 'Trade Payable', 4, 'Credit', true, false, 'Active', '应付账款'),

-- GST/HST Payable 下面的叶子
('21202121-2121-2121-2121-212121212121', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '21202120-2120-2120-2120-212021202120', '2121', 'GST/HST Payable', 4, 'Credit', true, false, 'Active', 'GST/HST应付'),

-- Payroll Liabilities 下面的叶子
('21302131-2131-2131-2131-213121312131', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '21302130-2130-2130-2130-213021302130', '2131', 'Payroll Liabilities', 4, 'Credit', true, false, 'Active', '工资负债'),

-- Bank Loans 下面的叶子
('22102211-2211-2211-2211-221122112211', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '22102210-2210-2210-2210-221022102210', '2211', 'Bank Loan', 4, 'Credit', true, false, 'Active', '银行贷款'),

-- Owner Contributions 下面的叶子
('31103111-3111-3111-3111-311131113111', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '31103110-3110-3110-3110-311031103110', '3111', 'Owner Contributions', 4, 'Credit', true, false, 'Active', '所有者投入'),

-- Owner Draws 下面的叶子
('31203121-3121-3121-3121-312131213121', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '31203120-3120-3120-3120-312031203120', '3121', 'Owner Draws', 4, 'Debit', true, false, 'Active', '所有者提款'),

-- Retained Earnings 下面的叶子
('31303131-3131-3131-3131-313131313131', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '31303130-3130-3130-3130-313031303130', '3131', 'Retained Earnings', 4, 'Credit', true, false, 'Active', '留存收益'),

-- Business Income 下面的叶子
('41104111-4111-4111-4111-411141114111', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '41104110-4110-4110-4110-411041104110', '4111', 'Business Income', 4, 'Credit', true, false, 'Active', '营业收入'),

-- Professional Fees Revenue 下面的叶子
('41204121-4121-4121-4121-412141214121', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '41204120-4120-4120-4120-412041204120', '4121', 'Professional Fees', 4, 'Credit', true, false, 'Active', '专业服务收入'),

-- Advertising 下面的叶子
('51105111-5111-5111-5111-511151115111', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '51105110-5110-5110-5110-511051105110', '5111', 'Advertising Expense', 4, 'Debit', true, false, 'Active', '广告费'),

-- Meals and Entertainment 下面的叶子
('51205121-5121-5121-5121-512151215121', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '51205120-5120-5120-5120-512051205120', '5121', 'Meals & Entertainment', 4, 'Debit', true, false, 'Active', '餐饮娱乐'),

-- Insurance 下面的叶子
('51305131-5131-5131-5131-513151315131', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '51305130-5130-5130-5130-513051305130', '5131', 'Insurance Expense', 4, 'Debit', true, false, 'Active', '保险费'),

-- Rent 下面的叶子
('51405141-5141-5141-5141-514151415141', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '51405140-5140-5140-5140-514051405140', '5141', 'Rent Expense', 4, 'Debit', true, false, 'Active', '租金'),

-- Salaries and Benefits 下面的叶子
('51505151-5151-5151-5151-515151515151', 'aa62b29b-5c6a-4aa7-9bf2-86644419518b', '51505150-5150-5150-5150-515051505150', '5151', 'Salaries Expense', 4, 'Debit', true, false, 'Active', '工资福利');