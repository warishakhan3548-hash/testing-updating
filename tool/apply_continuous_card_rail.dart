import 'dart:io';

void main() {
  final File mainFile = File('lib/main.dart');
  String source = mainFile.readAsStringSync();

  const String oldRail = '''  Path _rail(Size size) {
    final double r = math.min(radius, size.height / 2);
    final Path path = Path()
      ..moveTo(r * .72, 0)
      ..quadraticBezierTo(0, 0, 0, r)
      ..lineTo(0, size.height - r)
      ..quadraticBezierTo(0, size.height, r * .72, size.height);
    return path;
  }
''';

  const String newRail = '''  Path _rail(Size size) {
    final double r = math.min(radius, size.height / 2);

    // Keep the whole stroke inside the rounded clip and away from the avatar.
    // Drawing on x=0 clips half of a stroked path and can make the rail look
    // broken at the rounded turns on some pixel ratios.
    final double inset = UIConstants.accentStroke / 2 + 3;
    final double reach = math.min(6.5, math.max(4.5, r * .28));
    final double top = inset;
    final double bottom = math.max(top, size.height - inset);
    final double upperTurn = math.min(bottom, math.max(top, r));
    final double lowerTurn =
        math.max(upperTurn, math.min(bottom, size.height - r));

    return Path()
      ..moveTo(inset + reach, top)
      ..quadraticBezierTo(inset, top, inset, upperTurn)
      ..lineTo(inset, lowerTurn)
      ..quadraticBezierTo(inset, bottom, inset + reach, bottom);
  }
''';

  if (!source.contains(oldRail)) {
    stderr.writeln('Expected _CardAccentPainter rail block was not found.');
    exitCode = 2;
    return;
  }
  source = source.replaceFirst(oldRail, newRail);
  mainFile.writeAsStringSync(source);

  final File testFile = File('test/ui_micro_aesthetics_test.dart');
  String test = testFile.readAsStringSync();
  const String anchor = '''    // Brand/state color logic and Firebase integration must stay untouched.
''';
  const String guard = '''    // Card accent rail stays fully inside the clip and remains uninterrupted.
    expect(
      source,
      contains('final double inset = UIConstants.accentStroke / 2 + 3;'),
    );
    expect(source, contains('final double reach = math.min(6.5'));
    expect(source, contains('..lineTo(inset, lowerTurn)'));
    expect(source, isNot(contains('..lineTo(0, size.height - r)')));

''';
  if (!test.contains(anchor)) {
    stderr.writeln('Expected UI regression-test anchor was not found.');
    exitCode = 3;
    return;
  }
  test = test.replaceFirst(anchor, '$guard$anchor');
  testFile.writeAsStringSync(test);
}
