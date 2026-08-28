from pathlib import Path

path = Path("lib/main.dart")
text = path.read_text(encoding="utf-8")


def replace_exact(old: str, new: str, expected: int = 1, label: str = "") -> None:
    global text
    count = text.count(old)
    if count != expected:
        raise SystemExit(
            f"{label or old[:60]}: expected {expected} match(es), found {count}"
        )
    text = text.replace(old, new)


def patch_section(start_marker: str, end_marker: str, replacements, label: str) -> None:
    global text
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    chunk = text[start:end]
    for old, new, expected in replacements:
        count = chunk.count(old)
        if count != expected:
            raise SystemExit(
                f"{label}: expected {expected} match(es) for {old!r}, found {count}"
            )
        chunk = chunk.replace(old, new)
    text = text[:start] + chunk + text[end:]


replace_exact(
    "const Color lightCanvas = Color(0xFFF5F5F7);",
    "const Color lightCanvas = Color(0xFFF8FBFF);",
    label="light canvas",
)

replace_exact(
    "const List<_TabSpec> _tabs = <_TabSpec>[\n"
    "  _TabSpec('Home', Icons.home_rounded, appleBlue),\n"
    "  _TabSpec('Milk', Icons.local_drink_rounded, appleBlue),\n"
    "  _TabSpec('Credit', Icons.volunteer_activism_rounded, appleBlue),\n"
    "  _TabSpec('Expenses', Icons.receipt_long_rounded, semanticRed),\n"
    "  _TabSpec('Salary', Icons.payments_rounded, appleBlue),\n"
    "  _TabSpec('Diary', Icons.menu_book_rounded, diaryOrange),\n"
    "  _TabSpec('Business', Icons.work_rounded, appleBlue),\n"
    "];",
    "const List<_TabSpec> _tabs = <_TabSpec>[\n"
    "  _TabSpec('Home', Icons.home_rounded, appleBlue),\n"
    "  _TabSpec('Milk', Icons.local_drink_rounded, appleGreen),\n"
    "  _TabSpec('Credit', Icons.volunteer_activism_rounded, appleGreen),\n"
    "  _TabSpec('Expenses', Icons.receipt_long_rounded, appleBlue),\n"
    "  _TabSpec('Salary', Icons.payments_rounded, salaryGreen),\n"
    "  _TabSpec('Diary', Icons.menu_book_rounded, diaryOrange),\n"
    "  _TabSpec('Business', Icons.work_rounded, appleBlue),\n"
    "];",
    label="module identity colors",
)

replace_exact(
    "List<Color> _moduleTabColors(Map<String, dynamic> state) => <Color>[\n"
    "      appleBlue,\n"
    "      _tone(_milkGlobalNet(state)),\n"
    "      _tone(_creditGlobalNet(state)),\n"
    "      semanticRed,\n"
    "      _tone(_salaryGlobalNet(state)),\n"
    "      diaryOrange,\n"
    "      appleBlue,\n"
    "    ];",
    "List<Color> _moduleTabColors(Map<String, dynamic> state) => const <Color>[\n"
    "      appleBlue,\n"
    "      appleGreen,\n"
    "      appleGreen,\n"
    "      appleBlue,\n"
    "      salaryGreen,\n"
    "      diaryOrange,\n"
    "      appleBlue,\n"
    "    ];",
    label="stable navigation colors",
)

patch_section(
    "ThemeData _theme(Brightness brightness) {",
    "class _AmbientBackground",
    [
        (
            "inputDecorationTheme: InputDecorationTheme(\n"
            "      filled: true,\n"
            "      fillColor: dark\n"
            "          ? const Color(0x2E767680)\n"
            "          : const Color(0x17767680),\n"
            "      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 15),\n"
            "      hintStyle: const TextStyle(color: systemGray, fontWeight: FontWeight.w500),\n"
            "      labelStyle: const TextStyle(fontWeight: FontWeight.w700),\n"
            "      prefixIconColor: appleBlue,\n"
            "      border: OutlineInputBorder(\n"
            "        borderRadius: BorderRadius.circular(16),\n"
            "        borderSide: BorderSide(color: outline),\n"
            "      ),\n"
            "      enabledBorder: OutlineInputBorder(\n"
            "        borderRadius: BorderRadius.circular(16),\n"
            "        borderSide: BorderSide(color: outline),\n"
            "      ),\n"
            "      focusedBorder: OutlineInputBorder(\n"
            "        borderRadius: BorderRadius.circular(16),\n"
            "        borderSide: const BorderSide(color: appleBlue, width: 1.4),\n"
            "      ),\n"
            "    ),",
            "inputDecorationTheme: InputDecorationTheme(\n"
            "      filled: true,\n"
            "      fillColor: dark ? const Color(0x2EFFFFFF) : const Color(0xE8FFFFFF),\n"
            "      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 19),\n"
            "      hintStyle: const TextStyle(\n"
            "        color: systemGray,\n"
            "        fontSize: 16.5,\n"
            "        fontWeight: FontWeight.w600,\n"
            "      ),\n"
            "      labelStyle: const TextStyle(fontSize: 15.5, fontWeight: FontWeight.w700),\n"
            "      prefixIconColor: appleBlue,\n"
            "      border: OutlineInputBorder(\n"
            "        borderRadius: BorderRadius.circular(20),\n"
            "        borderSide: BorderSide(color: outline),\n"
            "      ),\n"
            "      enabledBorder: OutlineInputBorder(\n"
            "        borderRadius: BorderRadius.circular(20),\n"
            "        borderSide: BorderSide(\n"
            "          color: dark ? Colors.white.withAlpha(34) : appleBlue.withAlpha(34),\n"
            "        ),\n"
            "      ),\n"
            "      focusedBorder: OutlineInputBorder(\n"
            "        borderRadius: BorderRadius.circular(20),\n"
            "        borderSide: const BorderSide(color: appleBlue, width: 1.5),\n"
            "      ),\n"
            "    ),",
            1,
        )
    ],
    "reference input theme",
)

patch_section(
    "class _ScreenHeader extends StatelessWidget {",
    "class _CircleAction extends StatelessWidget {",
    [
        (
            "color: dark ? const Color(0xC7000000) : const Color(0xD1F5F5F7),",
            "color: dark ? const Color(0xD6000000) : const Color(0xF2FFFFFF),",
            1,
        ),
        (
            "padding: const EdgeInsets.fromLTRB(20, 11, 16, 12),",
            "padding: const EdgeInsets.fromLTRB(24, 14, 20, 16),",
            1,
        ),
        (
            "fontSize: leading == null ? 25 : 20,",
            "fontSize: leading == null ? 30 : 26,",
            1,
        ),
    ],
    "reference header",
)

patch_section(
    "class _CircleAction extends StatelessWidget {",
    "class _BackCircle extends StatelessWidget {",
    [
        ("borderRadius: BorderRadius.circular(22),", "borderRadius: BorderRadius.circular(18),", 1),
        ("width: 40,\n            height: 40,", "width: 48,\n            height: 48,", 1),
        ("shape: BoxShape.circle,", "borderRadius: BorderRadius.circular(18),", 1),
        ("child: Icon(icon, size: 18, color: color),", "child: Icon(icon, size: 21, color: color),", 1),
    ],
    "reference header actions",
)

patch_section(
    "class _BackCircle extends StatelessWidget {",
    "class _SearchBox extends StatefulWidget {",
    [
        ("width: 40,\n          height: 40,", "width: 48,\n          height: 48,", 1),
        ("borderRadius: BorderRadius.circular(22),", "borderRadius: BorderRadius.circular(24),", 1),
    ],
    "reference back button",
)

patch_section(
    "class _PrimaryButton extends StatelessWidget {",
    "class _AmountHero extends StatelessWidget {",
    [
        ("compact ? 14 : 17", "compact ? 18 : 20", 2),
        ("height: compact ? 40 : 54,", "height: compact ? 50 : 58,", 1),
        ("horizontal: compact ? 15 : 20", "horizontal: compact ? 18 : 22", 1),
        ("size: compact ? 17 : 20", "size: compact ? 19 : 22", 1),
        ("fontSize: compact ? 13 : 15,", "fontSize: compact ? 15 : 17,", 1),
    ],
    "reference primary buttons",
)

patch_section(
    "class _SheetFrame extends StatelessWidget {",
    "Future<T?> _openSheet<T>",
    [
        (
            "borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),",
            "borderRadius: const BorderRadius.vertical(top: Radius.circular(36)),",
            1,
        ),
        ("            20,\n            10,\n            20,", "            24,\n            12,\n            24,", 1),
        ("width: 48,\n                  height: 6,", "width: 54,\n                  height: 6,", 1),
        ("const SizedBox(height: 22),", "const SizedBox(height: 26),", 1),
        ("fontSize: 23,", "fontSize: 30,", 1),
        ("const SizedBox(height: 20),", "const SizedBox(height: 24),", 1),
    ],
    "reference bottom sheet",
)

patch_section(
    "class _BottomLedgerNav extends StatelessWidget {",
    "class _Pressable extends StatefulWidget {",
    [
        ("height: 70,", "height: 86,", 1),
        ("width: 70,\n                        height: 58,", "width: 80,\n                        height: 72,", 1),
        ("borderRadius: BorderRadius.circular(16),", "borderRadius: BorderRadius.circular(20),", 2),
        ("size: 20,", "size: 27,", 1),
        ("fontSize: 9.5,", "fontSize: 12,", 1),
        ("const SizedBox(height: 3),", "const SizedBox(height: 4),", 2),
        ("width: active ? 34 : 0,\n                              height: 3,", "width: active ? 38 : 0,\n                              height: 4,", 1),
    ],
    "reference bottom navigation",
)

patch_section(
    "class _CreditScreenState extends State<CreditScreen> {",
    "class CreditDetailScreen extends StatelessWidget {",
    [
        ("title: 'Credit Entry',", "title: 'Credit / Loan Entry',", 1),
        (
            "final Color moduleColor = _tone(net);",
            "final Color moduleColor = appleGreen;\n    final Color balanceColor = _tone(net, neutral: appleGreen);",
            1,
        ),
        (
            "color: moduleColor,\n              ),\n              const SizedBox(height: 18),",
            "color: balanceColor,\n              ),\n              const SizedBox(height: 18),",
            1,
        ),
        (
            "const SizedBox(height: 13),\n"
            "            SegmentedButton<String>(\n"
            "              segments: const <ButtonSegment<String>>[\n"
            "                ButtonSegment<String>(\n"
            "                  value: 'credit',\n"
            "                  label: Text('Given (+)'),\n"
            "                  icon: Icon(Icons.arrow_upward_rounded),\n"
            "                ),\n"
            "                ButtonSegment<String>(\n"
            "                  value: 'debit',\n"
            "                  label: Text('Taken (-)'),\n"
            "                  icon: Icon(Icons.arrow_downward_rounded),\n"
            "                ),\n"
            "              ],\n"
            "              selected: <String>{type},\n"
            "              onSelectionChanged: (Set<String> values) {\n"
            "                HapticFeedback.selectionClick();\n"
            "                setSheetState(() => type = values.first);\n"
            "              },\n"
            "            ),\n"
            "            const SizedBox(height: 20),\n"
            "            _PrimaryButton(\n"
            "              label: type == 'credit' ? 'Save Given' : 'Save Taken',\n"
            "              color: type == 'credit' ? appleGreen : appleRed,\n"
            "              onTap: () => Navigator.pop(sheetContext, true),\n"
            "            ),",
            "const SizedBox(height: 22),\n"
            "            Row(\n"
            "              children: <Widget>[\n"
            "                Expanded(\n"
            "                  child: _PrimaryButton(\n"
            "                    label: 'Given',\n"
            "                    icon: Icons.add_rounded,\n"
            "                    color: appleGreen,\n"
            "                    onTap: () {\n"
            "                      type = 'credit';\n"
            "                      Navigator.pop(sheetContext, true);\n"
            "                    },\n"
            "                  ),\n"
            "                ),\n"
            "                const SizedBox(width: 12),\n"
            "                Expanded(\n"
            "                  child: _PrimaryButton(\n"
            "                    label: 'Taken',\n"
            "                    icon: Icons.remove_rounded,\n"
            "                    color: appleRed,\n"
            "                    onTap: () {\n"
            "                      type = 'debit';\n"
            "                      Navigator.pop(sheetContext, true);\n"
            "                    },\n"
            "                  ),\n"
            "                ),\n"
            "              ],\n"
            "            ),",
            1,
        ),
    ],
    "reference credit sheet",
)

replace_exact("title: 'Salary Entry',", "title: 'Add Salary Entry',", label="salary sheet title")
replace_exact("label: 'Create Account',", "label: 'Create Khata',", label="business create button")

patch_section(
    "class ExpenseScreen extends StatefulWidget {",
    "class ExpenseDetailScreen extends StatefulWidget {",
    [
        (
            "title: 'Expenses',\n          color: semanticRed,",
            "title: 'Expenses',\n          color: appleBlue,",
            1,
        ),
        (
            "label: 'Month Expense',\n                value: _money(total),\n                color: semanticRed,",
            "label: 'Month Expense',\n                value: _money(total),\n                color: appleBlue,",
            1,
        ),
    ],
    "reference expense colors",
)

path.write_text(text, encoding="utf-8")
