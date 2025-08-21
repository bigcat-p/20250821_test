import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QCheckBox,
    QGroupBox,
    QTextEdit,
    QScrollArea,
    QFrame,
    QMessageBox,
    QLayoutItem,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCursor


# 复用核心计算逻辑（保持不变）
def get_positive_number(value_str, prompt):
    try:
        value = float(value_str)
        if value > 0:
            return value, None
        return None, f"{prompt}必须是正数！"
    except ValueError:
        return None, f"{prompt}必须是有效的数字！"


def get_positive_integer(value_str, prompt):
    try:
        value = int(value_str)
        if value > 0:
            return value, None
        return None, f"{prompt}必须是正整数！"
    except ValueError:
        return None, f"{prompt}必须是有效的整数！"


def calculate_defense(initial_defense, pets, persons, max_rounds=30):
    current_defense = initial_defense
    rounds = 0
    log = []

    for pet in pets:
        pet["percent_effects"] = {}
        pet["fixed_effects"] = {}
    for person in persons:
        person["effects"] = {}

    log.append(f"===== 计算开始 =====")
    log.append(f"初始防御值: {int(initial_defense)}，最多计算{max_rounds}回合\n")

    while rounds < max_rounds:
        rounds += 1
        log.append(f"\n===== 回合 {rounds} =====")
        log.append(f"回合开始时防御: {int(current_defense)}")

        # 宠物效果回弹
        for pet_idx, pet in enumerate(pets, 1):
            expire_round = rounds - pet["percent_duration"]
            if expire_round in pet["percent_effects"]:
                rebound = pet["percent_effects"][expire_round]
                current_defense += rebound
                log.append(
                    f"第{expire_round}回合宠物{pet_idx}百分比效果消失，回弹 {int(rebound)}，防御变为: {int(current_defense)}"
                )
                del pet["percent_effects"][expire_round]

            if pet["use_fixed"]:
                expire_round = rounds - pet["fixed_duration"]
                if expire_round in pet["fixed_effects"]:
                    rebound = pet["fixed_effects"][expire_round]
                    current_defense += rebound
                    log.append(
                        f"第{expire_round}回合宠物{pet_idx}固定效果消失，回弹 {int(rebound)}，防御变为: {int(current_defense)}"
                    )
                    del pet["fixed_effects"][expire_round]

        # 人物效果回弹
        for person_idx, person in enumerate(persons, 1):
            expire_round = rounds - person["duration"]
            if expire_round in person["effects"]:
                rebound = person["effects"][expire_round]
                current_defense += rebound
                log.append(
                    f"第{expire_round}回合人物{person_idx}效果消失，回弹 {int(rebound)}，防御变为: {int(current_defense)}"
                )
                del person["effects"][expire_round]

        if current_defense <= 0:
            log.append(f"\n回合 {rounds} 结束，防御已降至0！")
            return "\n".join(log), rounds, 0

        # 宠物释放技能
        for pet_idx, pet in enumerate(pets, 1):
            reduce_percent = current_defense * pet["percent"]
            current_defense -= reduce_percent
            log.append(
                f"宠物{pet_idx}攻击，百分比降低 {int(reduce_percent)} ({pet['percent']*100}%)，防御变为: {int(current_defense)}"
            )
            pet["percent_effects"][rounds] = reduce_percent

            if current_defense <= 0:
                log.append(f"\n回合 {rounds} 结束，防御已降至0！")
                return "\n".join(log), rounds, 0

            if pet["use_fixed"]:
                reduce_fixed = min(pet["fixed"], current_defense)
                current_defense -= reduce_fixed
                log.append(
                    f"宠物{pet_idx}攻击，固定降低 {int(reduce_fixed)}，防御变为: {int(current_defense)}"
                )
                pet["fixed_effects"][rounds] = reduce_fixed

                if current_defense <= 0:
                    log.append(f"\n回合 {rounds} 结束，防御已降至0！")
                    return "\n".join(log), rounds, 0

        # 人物释放技能
        for person_idx, person in enumerate(persons, 1):
            reduce_fixed = min(person["fixed"], current_defense)
            current_defense -= reduce_fixed
            log.append(
                f"人物{person_idx}攻击，降低 {int(reduce_fixed)}，防御变为: {int(current_defense)}"
            )
            person["effects"][rounds] = reduce_fixed

            if current_defense <= 0:
                log.append(f"\n回合 {rounds} 结束，防御已降至0！")
                return "\n".join(log), rounds, 0

        log.append(f"回合 {rounds} 结束，当前防御: {int(current_defense)}")

    log.append(f"\n===== 计算结束 =====")
    log.append(f"经过 {max_rounds} 回合后，最终防御值为 {int(current_defense)}")
    return "\n".join(log), rounds, current_defense


# GUI 界面类（修复动态表单更新问题）
class DefenseCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pet_frames = []  # 存储宠物参数输入框的容器
        self.person_frames = []  # 存储人物参数输入框的容器
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("防御降低计算器")
        self.setGeometry(100, 100, 1000, 800)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # 1. 基础参数区域
        base_group = QGroupBox("基础参数")
        base_layout = QHBoxLayout()
        base_group.setLayout(base_layout)

        base_layout.addWidget(QLabel("初始防御值:"))
        self.initial_defense_input = QLineEdit()
        self.initial_defense_input.setPlaceholderText("请输入正数")
        base_layout.addWidget(self.initial_defense_input)

        base_layout.addWidget(QLabel("宠物数量:"))
        self.pet_count = QSpinBox()
        self.pet_count.setMinimum(1)
        self.pet_count.setMaximum(5)
        self.pet_count.valueChanged.connect(self.update_pet_forms)
        base_layout.addWidget(self.pet_count)

        base_layout.addWidget(QLabel("人物数量:"))
        self.person_count = QSpinBox()
        self.person_count.setMinimum(1)
        self.person_count.setMaximum(5)
        self.person_count.valueChanged.connect(self.update_person_forms)
        base_layout.addWidget(self.person_count)

        main_layout.addWidget(base_group)

        # 2. 宠物参数区域
        self.pet_scroll = QScrollArea()
        self.pet_scroll.setWidgetResizable(True)
        self.pet_container = QWidget()
        self.pet_layout = QVBoxLayout(self.pet_container)
        self.pet_scroll.setWidget(self.pet_container)
        main_layout.addWidget(QLabel("宠物参数设置:"))
        main_layout.addWidget(self.pet_scroll)

        # 3. 人物参数区域
        self.person_scroll = QScrollArea()
        self.person_scroll.setWidgetResizable(True)
        self.person_container = QWidget()
        self.person_layout = QVBoxLayout(self.person_container)
        self.person_scroll.setWidget(self.person_container)
        main_layout.addWidget(QLabel("人物参数设置:"))
        main_layout.addWidget(self.person_scroll)

        # 4. 计算按钮
        self.calc_btn = QPushButton("开始计算")
        self.calc_btn.clicked.connect(self.start_calculation)
        main_layout.addWidget(self.calc_btn)

        # 5. 结果显示区域
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(QFont("SimHei", 10))
        main_layout.addWidget(QLabel("计算结果:"))
        main_layout.addWidget(self.result_text)

        # 初始生成表单
        self.update_pet_forms()
        self.update_person_forms()

    def update_pet_forms(self):
        """修复：正确清理旧表单，避免引用冲突"""
        # 关键修复：从布局中彻底移除并删除所有旧部件
        # 遍历布局中的所有项，移除并删除
        while self.pet_layout.count():
            item = self.pet_layout.takeAt(0)  # 移除布局中的项
            widget = item.widget()
            if widget:
                widget.deleteLater()  # 删除部件
            # 处理子布局（如果有的话）
            layout = item.layout()
            if layout:
                while layout.count():
                    sub_item = layout.takeAt(0)
                    sub_widget = sub_item.widget()
                    if sub_widget:
                        sub_widget.deleteLater()
        self.pet_frames.clear()  # 清空存储的输入框引用

        # 生成新表单
        count = self.pet_count.value()
        for i in range(count):
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            layout = QHBoxLayout(frame)
            layout.setContentsMargins(5, 5, 5, 5)  # 减少内边距，避免拥挤

            layout.addWidget(QLabel(f"宠物 {i+1}:"), alignment=Qt.AlignLeft)

            # 百分比降低
            layout.addWidget(QLabel("百分比降低(%)"), alignment=Qt.AlignLeft)
            percent_input = QLineEdit()
            percent_input.setPlaceholderText("如20表示20%")
            percent_input.setMaximumWidth(100)
            layout.addWidget(percent_input)

            # 百分比持续回合
            layout.addWidget(QLabel("持续回合"), alignment=Qt.AlignLeft)
            percent_duration = QLineEdit()
            percent_duration.setPlaceholderText("正整数")
            percent_duration.setMaximumWidth(80)
            layout.addWidget(percent_duration)

            # 固定效果开关
            use_fixed = QCheckBox("启用固定降低")
            use_fixed.setChecked(False)
            layout.addWidget(use_fixed, alignment=Qt.AlignLeft)

            # 固定降低值
            fixed_input = QLineEdit()
            fixed_input.setPlaceholderText("固定值")
            fixed_input.setMaximumWidth(100)
            fixed_input.setEnabled(False)
            layout.addWidget(fixed_input)

            # 固定效果持续回合
            fixed_duration = QLineEdit()
            fixed_duration.setPlaceholderText("持续回合")
            fixed_duration.setMaximumWidth(80)
            fixed_duration.setEnabled(False)
            layout.addWidget(fixed_duration)

            # 勾选开关时启用固定输入框
            def toggle_fixed(checked, fixed, dur):
                fixed.setEnabled(checked)
                dur.setEnabled(checked)

            use_fixed.stateChanged.connect(
                lambda checked, f=fixed_input, d=fixed_duration: toggle_fixed(
                    checked, f, d
                )
            )

            self.pet_frames.append(
                {
                    "percent_input": percent_input,
                    "percent_duration": percent_duration,
                    "use_fixed": use_fixed,
                    "fixed_input": fixed_input,
                    "fixed_duration": fixed_duration,
                }
            )

            self.pet_layout.addWidget(frame)

        self.pet_layout.addStretch()  # 保持表单顶部对齐

    def update_person_forms(self):
        """修复：正确清理旧表单"""
        # 关键修复：彻底移除旧部件
        while self.person_layout.count():
            item = self.person_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            layout = item.layout()
            if layout:
                while layout.count():
                    sub_item = layout.takeAt(0)
                    sub_widget = sub_item.widget()
                    if sub_widget:
                        sub_widget.deleteLater()
        self.person_frames.clear()

        # 生成新表单
        count = self.person_count.value()
        for i in range(count):
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            layout = QHBoxLayout(frame)
            layout.setContentsMargins(5, 5, 5, 5)

            layout.addWidget(QLabel(f"人物 {i+1}:"), alignment=Qt.AlignLeft)

            # 固定降低值
            layout.addWidget(QLabel("固定降低值"), alignment=Qt.AlignLeft)
            fixed_input = QLineEdit()
            fixed_input.setPlaceholderText("请输入正数")
            fixed_input.setMaximumWidth(100)
            layout.addWidget(fixed_input)

            # 持续回合
            layout.addWidget(QLabel("持续回合"), alignment=Qt.AlignLeft)
            duration_input = QLineEdit()
            duration_input.setPlaceholderText("正整数")
            duration_input.setMaximumWidth(80)
            layout.addWidget(duration_input)

            self.person_frames.append(
                {"fixed_input": fixed_input, "duration_input": duration_input}
            )

            self.person_layout.addWidget(frame)

        self.person_layout.addStretch()

    def start_calculation(self):
        """收集参数并计算（逻辑不变）"""
        # 验证初始防御值
        initial_defense, err = get_positive_number(
            self.initial_defense_input.text(), "初始防御值"
        )
        if err:
            QMessageBox.warning(self, "输入错误", err)
            return

        # 收集宠物参数
        pets = []
        for i, pet_frame in enumerate(self.pet_frames, 1):
            # 百分比降低
            percent_str = pet_frame["percent_input"].text()
            percent, err = get_positive_number(percent_str, f"宠物{i}百分比降低值")
            if err:
                QMessageBox.warning(self, "输入错误", err)
                return
            percent /= 100

            # 百分比持续回合
            percent_duration_str = pet_frame["percent_duration"].text()
            percent_duration, err = get_positive_integer(
                percent_duration_str, f"宠物{i}百分比效果持续回合"
            )
            if err:
                QMessageBox.warning(self, "输入错误", err)
                return

            # 固定效果参数
            use_fixed = pet_frame["use_fixed"].isChecked()
            fixed = 0
            fixed_duration = 0
            if use_fixed:
                fixed_str = pet_frame["fixed_input"].text()
                fixed, err = get_positive_number(fixed_str, f"宠物{i}固定降低值")
                if err:
                    QMessageBox.warning(self, "输入错误", err)
                    return

                fixed_duration_str = pet_frame["fixed_duration"].text()
                fixed_duration, err = get_positive_integer(
                    fixed_duration_str, f"宠物{i}固定效果持续回合"
                )
                if err:
                    QMessageBox.warning(self, "输入错误", err)
                    return

            pets.append(
                {
                    "percent": percent,
                    "percent_duration": percent_duration,
                    "use_fixed": use_fixed,
                    "fixed": fixed,
                    "fixed_duration": fixed_duration,
                }
            )

        # 收集人物参数
        persons = []
        for i, person_frame in enumerate(self.person_frames, 1):
            fixed_str = person_frame["fixed_input"].text()
            fixed, err = get_positive_number(fixed_str, f"人物{i}固定降低值")
            if err:
                QMessageBox.warning(self, "输入错误", err)
                return

            duration_str = person_frame["duration_input"].text()
            duration, err = get_positive_integer(duration_str, f"人物{i}效果持续回合")
            if err:
                QMessageBox.warning(self, "输入错误", err)
                return

            persons.append({"fixed": fixed, "duration": duration})

        # 执行计算并显示结果
        log, rounds, final = calculate_defense(initial_defense, pets, persons)
        self.result_text.setText(log)
        self.result_text.moveCursor(QTextCursor.Start)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("SimHei"))  # 确保中文显示
    window = DefenseCalculator()
    window.show()
    sys.exit(app.exec_())
