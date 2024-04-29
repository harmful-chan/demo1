import sys
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal, Qt
from PyQt5.uic import loadUi
from io import StringIO
from gui import Ui_Dialog

import os
import time
from datetime import datetime

from deduction_marked import send_out
from script_deduct_money import is_exists, BASE_DIR, get_distribution_costs, deduct_money, audit_teller, shipped
from user_info.scripts import save
from wlog import setup_logging



class WorkerThread(QThread):
    progress_changed = pyqtSignal(int)
    log_updated = pyqtSignal(str)
    output_updated = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, input_text, in_cost_content):
        super().__init__()
        self.input_text = input_text
        self.in_cost_content = in_cost_content
        self.log_buffer = StringIO()

    def run(self):
        sys.stdout = self.log_buffer
        sys.stderr = self.log_buffer

        self.log_updated.emit('开始运行')
        self.main(self.input_text, self.in_cost_content)
        log_content = self.log_buffer.getvalue()
        self.log_updated.emit(f'{log_content}{"结束":-^40}')
        self.finished.emit('完成')

    def main(self, in_o, in_cost_content):
        now = datetime.now().strftime('%Y年%m月%d日')
        log_path = os.path.join(BASE_DIR, f'日志\\日志总的.txt')
        logger = setup_logging(log_path)

        leaflet = False
        o_split = in_o.strip().split('\n')
        is_leaflet = len(o_split[0].split()[1])
        if is_leaflet > 10:
            in_o_list = o_split
            leaflet = True
            logger.info(f'正在处理的是，促销单')
            # self.log_updated.emit(f'正在处理的是，促销单')
        else:
            in_o_list = [' '.join(item.split()[::2]) for item in o_split]

        temp, cookie = '', ''
        admin_cookie = is_exists('admin')
        res_list = [''] * len(in_o_list)
        total_steps = len(in_o_list)

        record_path = os.path.join('D:\\我的坚果云\\数据采集\\扣款记录', now)
        f_tx_path = os.path.join(BASE_DIR, f'日志\\提现总的.txt')
        logger_tx = setup_logging(f_tx_path, print_=False)
        log_dir_last = os.path.join(BASE_DIR, '日志', '上次')
        os.makedirs(log_dir_last, exist_ok=True)
        os.makedirs(record_path, exist_ok=True)

        index = 0
        current_step = 0
        gap = None
        o_status = ''
        text_last = ''
        pass_company_code = None
        while index < len(in_o_list):
            try:
                item = in_o_list[index]
                if leaflet:
                    company_code, order_code, tracking_number, logistics = item.split()
                else:
                    company_code, order_code = item.split()

                if pass_company_code == company_code:
                    logger.info(f'此 {company_code} 有出纳报错无法处理，跳过')
                    # self.log_updated.emit(f'此 {company_code} 有出纳报错无法处理，跳过')
                    res_list[index] = f'此 {company_code} 有出纳报错无法处理，跳过'
                    # self.output_updated.emit(f'此 {company_code} 有出纳报错无法处理，跳过')
                    continue

                template = company_code + ' ' + order_code
                f_last_path = os.path.join(log_dir_last, f'{company_code}.txt')
                if temp != company_code:
                    cookie = is_exists(company_code)

                # 分销成本
                costs_info = get_distribution_costs(cookie, order_code)
                if costs_info == '重新登录':
                    cookie = save.login_save_cookie(company_code)
                    costs_info = get_distribution_costs(cookie, order_code)

                if type(costs_info) is not dict:
                    res_list[index] = costs_info
                    logger.info(template + ' ' + costs_info)
                    # self.log_updated.emit(template + ' ' + costs_info)
                    # self.output_updated.emit(costs_info)
                    continue

                o_status, order_id, cost = costs_info.values()

                if in_cost_content:
                    cost = str(in_cost_content)
                    logger.info(template + f' 手动扣款金额 {cost}')
                    # self.log_updated.emit(template + f' 手动扣款金额 {cost}')

                elif eval(cost) == 0:
                    res_list[index] = 'erp中成本为零无法扣除'
                    logger.info(template + ' erp中成本为零无法扣除')
                    # self.log_updated.emit(template + ' erp中成本为零无法扣除')
                    # self.output_updated.emit('erp中成本为零无法扣除')
                    continue

                # 提现
                deduct_info = deduct_money(company_code, cookie, cost)
                time.sleep(1)
                deduct_info_err = deduct_info.get('error')
                transaction_no_tx = deduct_info.get('transaction_no_tx')
                if transaction_no_tx:
                    with open(f_last_path, 'a+', encoding='utf-8') as f:
                        f.seek(0)
                        txt = f.readline().split()
                        if txt:
                            transaction_no_tx_last = txt[-1]
                            if transaction_no_tx != transaction_no_tx_last:
                                f.truncate(0)
                                logger_tx.info(template + ' ' + o_status + ' ' + transaction_no_tx + ' ' + cost)
                                f.write(str(index) + ' ' + template + ' ' + o_status + ' ' + transaction_no_tx)
                        else:
                            logger_tx.info(template + ' ' + o_status + ' ' + transaction_no_tx + ' ' + cost)
                            f.write(str(index) + ' ' + template + ' ' + o_status + ' ' + transaction_no_tx)

                if deduct_info_err:
                    if '还在审核中' in deduct_info_err:
                        logger.info(f'有未审核的，当前订单 [{index} {template} {o_status}]')
                        # self.log_updated.emit(f'有未审核的，当前订单 [{index} {template} {o_status}]')
                        with open(f_last_path, 'r', encoding='utf-8') as f:
                            text = f.readline().split()
                            index_last = text[0]
                            company_code_last = text[1]
                            order_code_last = text[2]
                            o_status = text[3]
                            transaction_no_tx = text[-1]
                            company_code = company_code_last
                            template = company_code_last + ' ' + order_code_last

                            if text == text_last or index < int(index_last) or int(index_last) == 0:
                                if order_code_last != order_code:
                                    pass_company_code = company_code_last
                                    res_list[index] = f'此 {company_code} 有出纳报错无法处理，跳过'
                                    logger.info(f'此 {text} 无法处理，跳过。')
                                    # self.log_updated.emit(f'此 {text} 无法处理，跳过。')
                                    # self.output_updated.emit(f'此 {company_code} 有出纳报错无法处理，跳过')
                                    continue
                                else:
                                    index_last = index

                            logger.info(f'优先处理上次还在审核中的 {text}')
                            # self.log_updated.emit(f'优先处理上次还在审核中的 {text}')

                            gap = index - int(index_last)
                            index = int(index_last)
                            text_last = text
                    else:
                        res_list[index] = deduct_info_err
                        logger.info(template + ' ' + o_status + ' ' + deduct_info_err)
                        # self.log_updated.emit(template + ' ' + o_status + ' ' + deduct_info_err)
                        # self.output_updated.emit(deduct_info_err)
                        current_step += 1
                        # self.progress_changed.emit(int((current_step / total_steps) * 100))
                        continue

                # 审核出纳
                audit_teller_info = audit_teller(admin_cookie, transaction_no_tx)
                e_message = audit_teller_info.get('error')
                if e_message:
                    if e_message == '不存在该用户':
                        admin_cookie = save.login_save_cookie('admin')
                        audit_teller_info = audit_teller(admin_cookie, transaction_no_tx)
                    elif e_message == '拒绝审核成功':
                        logger.info(template + ' ' + o_status + ' ' + e_message + ' ' + '再次扣款')
                        # self.log_updated.emit(template + ' ' + o_status + ' ' + e_message + ' ' + '再次扣款')
                        index -= 1
                        continue
                    else:
                        res_list[index] = e_message
                        logger.error(template + ' ' + o_status + ' ' + e_message)
                        # self.log_updated.emit(template + ' ' + o_status + ' ' + e_message)
                        # self.output_updated.emit(e_message)
                        continue

                result = audit_teller_info['result']
                shipped_res = ''

                if o_status == '待发货审核':
                    shipped_res = shipped(cookie, order_id)

                if leaflet:
                    res_list[index] = result.split()[0]
                    send_res = send_out(cookie, order_id, logistics, tracking_number)
                    logger.info(template + ' ' + o_status + ' ' + result + ' ' + shipped_res + ' ' + send_res)
                    # self.log_updated.emit(template + ' ' + o_status + ' ' + result + ' ' + shipped_res + ' ' + send_res)
                    # self.output_updated.emit(result.split()[0])
                else:
                    res_list[index] = result
                    logger.info(template + ' ' + o_status + ' ' + result + ' ' + shipped_res)
                    # self.log_updated.emit(template + ' ' + o_status + ' ' + result + ' ' + shipped_res)
                    # self.output_updated.emit(result)

                with open(os.path.join(record_path, f'{order_code}.txt', ), 'a+', encoding='utf-8') as w_record:
                    t = datetime.now().strftime('%Y-%m-%d %H:%M')
                    w_record.write(t + ' - ' + template + ' ' + result + '\n')

                # self.progress_changed.emit(int((current_step / total_steps) * 100))

            except Exception as e:
                res_list[index] = template + ' ' + o_status + ' ' + str(e)
                logger.info(template + ' ' + o_status + ' ' + str(e))
                # self.log_updated.emit(template + ' ' + o_status + ' ' + str(e))
                # self.output_updated.emit(template + ' ' + o_status + ' ' + str(e))
                continue

            finally:
                current_step += 1
                temp = company_code
                
                if gap:
                    index += gap
                else:
                    index += 1

                with open(os.path.join(BASE_DIR, '日志/result.txt'), 'w') as f:
                    f.write('\n'.join(res_list))

                log_content = self.log_buffer.getvalue()
                self.log_updated.emit(log_content)
                self.output_updated.emit('\n'.join(res_list))
                self.progress_changed.emit(int((current_step / total_steps) * 100))
                
                
class MyDialog(QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # 加载你导出的UI文件
        self.setWindowTitle("扣款")
        self.run.clicked.connect(self.run_custom_function)  # 将按钮点击事件连接到自定义函数
        self.paste.clicked.connect(self.paste_from_clipboard)
        self.copy.clicked.connect(self.copy_to_clipboard)
        self.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

    @pyqtSlot()
    def run_custom_function(self):
        self.run.setDisabled(True)
        self.output.clear()
        self.logtext.clear()
        input_text = self.input.toPlainText()
        in_cost_content = self.in_cost.text()
        self.worker_thread = WorkerThread(input_text, in_cost_content)
        self.worker_thread.log_updated.connect(self.write_to_logtext)
        self.worker_thread.progress_changed.connect(self.update_progress_bar)
        self.worker_thread.output_updated.connect(self.write_to_output)
        self.worker_thread.finished.connect(self.handle_finished)
        self.worker_thread.start()


    @pyqtSlot(str)
    def handle_finished(self, result):
        self.in_cost.clear()
        self.run.setDisabled(False)

    @pyqtSlot(int)
    def update_progress_bar(self, value):
        self.progressBar.setValue(value)

    @pyqtSlot()
    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()  # 获取剪贴板对象
        clipboard_text = clipboard.text()  # 获取剪贴板中的文本内容
        self.input.setPlainText(clipboard_text)  # 将文本内容粘贴到输入框中

    @pyqtSlot()
    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()  # 获取剪贴板对象
        output_text = self.output.toPlainText()  # 获取输出框中的文本内容
        clipboard.setText(output_text)  # 将文本内容设置到剪贴板中

    def write_to_logtext(self, message):
        self.logtext.setPlainText(message)

    def write_to_output(self, message):
        self.output.setPlainText(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = MyDialog()
    dialog.show()
    sys.exit(app.exec_())
