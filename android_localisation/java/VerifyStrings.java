import java.io.*;
import java.util.*;
import java.util.regex.*;

/**
 * Utility to verify that all translated Android strings containing format specifiers
 * (like %1$d or %s) are syntactically valid and won't throw an UnknownFormatConversionException
 * or MissingFormatArgumentException at runtime.
 */
public class VerifyStrings {

    public static void main(String[] args) throws Exception {
        String resDirPath = "app/src/main/res";
        if (args.length > 0) {
            resDirPath = args[0];
        }

        File resDir = new File(resDirPath);
        if (!resDir.exists()) {
            File fallback = new File("../" + resDirPath);
            if (fallback.exists()) resDir = fallback;
        }

        if (!resDir.exists()) {
            System.err.println("Fatal: Could not find resource directory at: " + resDirPath);
            System.exit(1);
        }

        File englishDir = new File(resDir, "values");
        File[] valuesDirs = resDir.listFiles((dir, name) -> name.startsWith("values-"));

        if (valuesDirs == null || valuesDirs.length == 0) {
            System.out.println("No values-* localized directories found.");
            return;
        }

        System.out.println("Started Android String Format Verification...");
        System.out.println("Scanning source strings in: " + englishDir.getPath());

        // Parse English strings
        Map<String, String> englishStrings = parseStringsFile(new File(englishDir, "strings.xml"));
        Set<String> nonFormattedKeys = getNonFormattedKeys(new File(englishDir, "strings.xml"));

        // Build expected arg type list per key from English strings
        // e.g. "User %1$s has %2$d items at $%3$.2f" -> ['s', 'd', 'f']
        Map<String, List<Character>> expectedArgTypes = new HashMap<>();
        Pattern formatPattern = Pattern.compile("%(\\d+\\$)?([-#+ 0,(<]*)?(\\d+)?(\\.\\d+)?([tT]?[a-zA-Z])");

        for (Map.Entry<String, String> entry : englishStrings.entrySet()) {
            if (nonFormattedKeys.contains(entry.getKey())) continue;

            Map<Integer, Character> indexedTypes = new TreeMap<>();
            int autoIndex = 1;
            // Strip %% (escaped percent) before scanning — otherwise the second % followed by a
            // space-flag and a letter (e.g. "%% completed") gets misread as a format specifier.
            String valueToScan = entry.getValue().replace("%%", "");
            Matcher m = formatPattern.matcher(valueToScan);

            while (m.find()) {
                String convStr = m.group(5);
                if (convStr == null || convStr.equals("%") || convStr.equals("n")) continue;
                char conv = convStr.charAt(convStr.length() - 1);
                String indexGroup = m.group(1);
                if (indexGroup != null) {
                    int idx = Integer.parseInt(indexGroup.replace("$", ""));
                    indexedTypes.put(idx, conv);
                } else {
                    indexedTypes.put(autoIndex++, conv);
                }
            }

            if (!indexedTypes.isEmpty()) {
                List<Character> orderedTypes = new ArrayList<>();
                int maxIdx = Collections.max(indexedTypes.keySet());
                for (int i = 1; i <= maxIdx; i++) {
                    orderedTypes.add(indexedTypes.getOrDefault(i, 's'));
                }
                expectedArgTypes.put(entry.getKey(), orderedTypes);
            }
        }

        int totalErrors = 0;
        int totalStringsVerified = 0;

        for (File dir : valuesDirs) {
            File stringsFile = new File(dir, "strings.xml");
            if (!stringsFile.exists()) continue;

            Map<String, String> localizedStrings = parseStringsFile(stringsFile);
            Set<String> localNonFormatted = getNonFormattedKeys(stringsFile);

            for (Map.Entry<String, String> entry : localizedStrings.entrySet()) {
                String name = entry.getKey();
                String text = entry.getValue();
                totalStringsVerified++;

                // Skip strings explicitly marked as non-formatted in either English or translation
                if (nonFormattedKeys.contains(name) || localNonFormatted.contains(name)) continue;

                List<Character> argTypes = expectedArgTypes.get(name);
                if (argTypes == null || argTypes.isEmpty()) {
                    // No format args expected — a bare unescaped % is an error
                    String stripped = text.replace("%%", "");
                    if (stripped.contains("%")) {
                        System.err.println("ERROR: [" + dir.getName() + "] String '" + name
                                + "' contains unescaped % but English has no format args.");
                        System.err.println("  Text: " + text);
                        totalErrors++;
                    }
                    continue;
                }

                // Build correctly-typed args array based on what English string expects
                Object[] formatArgs = buildArgs(argTypes);

                try {
                    String.format(text, formatArgs);
                } catch (UnknownFormatConversionException e) {
                    System.err.println("CRASH: [" + dir.getName() + "] String '" + name
                            + "' has an invalid conversion specifier: " + e.getConversion());
                    System.err.println("  Text: " + text);
                    totalErrors++;
                } catch (MissingFormatArgumentException e) {
                    System.err.println("CRASH: [" + dir.getName() + "] String '" + name
                            + "' is missing format arguments or index is wrong: " + e.getFormatSpecifier());
                    System.err.println("  Text: " + text);
                    totalErrors++;
                } catch (IllegalFormatConversionException e) {
                    System.err.println("CRASH: [" + dir.getName() + "] String '" + name
                            + "' uses wrong type for a format specifier: " + e.getMessage());
                    System.err.println("  Text: " + text);
                    System.err.println("  English: " + englishStrings.get(name));
                    totalErrors++;
                } catch (Exception e) {
                    System.err.println("CRASH: [" + dir.getName() + "] String '" + name
                            + "' failed String.format() -> " + e.getClass().getSimpleName() + ": " + e.getMessage());
                    System.err.println("  Text: " + text);
                    totalErrors++;
                }
            }
        }

        System.out.println("Verification Complete!");
        System.out.println("Total Strings Verified: " + totalStringsVerified);

        if (totalErrors > 0) {
            System.out.println("Total Errors Found: " + totalErrors);
            System.err.println("Verification Failed!");
            System.exit(1);
        } else {
            System.out.println("Status: ALL STRINGS PASSED!");
            System.exit(0);
        }
    }

    /**
     * Builds an Object[] matching the arg types detected from the English string.
     * 's' -> String, 'd'/'i'/'o'/'x' -> Integer, 'f'/'e'/'g'/'a' -> Double, 'b' -> Boolean, 'c' -> Character
     */
    private static Object[] buildArgs(List<Character> argTypes) {
        Object[] args = new Object[argTypes.size()];
        for (int i = 0; i < argTypes.size(); i++) {
            char type = Character.toLowerCase(argTypes.get(i));
            switch (type) {
                case 'd': case 'i': case 'o': case 'x': args[i] = 42;      break;
                case 'f': case 'e': case 'g': case 'a': args[i] = 3.14;    break;
                case 'b':                               args[i] = true;     break;
                case 'c':                               args[i] = 'A';      break;
                default:                                args[i] = "test";   break;
            }
        }
        return args;
    }

    /**
     * Returns keys that have formatted="false" — their % signs are literal, not format specifiers.
     */
    private static Set<String> getNonFormattedKeys(File file) throws Exception {
        Set<String> keys = new HashSet<>();
        if (!file.exists()) return keys;
        String content = readFile(file);
        // Match both attribute orderings
        Pattern p1 = Pattern.compile("<string[^>]+name=\"([^\"]+)\"[^>]+formatted\\s*=\\s*\"false\"",
                Pattern.CASE_INSENSITIVE);
        Pattern p2 = Pattern.compile("<string[^>]+formatted\\s*=\\s*\"false\"[^>]+name=\"([^\"]+)\"",
                Pattern.CASE_INSENSITIVE);
        for (Pattern p : new Pattern[]{p1, p2}) {
            Matcher m = p.matcher(content);
            while (m.find()) keys.add(m.group(1));
        }
        return keys;
    }

    private static Map<String, String> parseStringsFile(File file) throws Exception {
        Map<String, String> strings = new LinkedHashMap<>();
        if (!file.exists()) return strings;
        String content = readFile(file);
        Pattern stringPattern = Pattern.compile(
                "<string\\s+[^>]*name=\"([^\"]+)\"[^>]*>(.*?)</string>", Pattern.DOTALL);
        Matcher m = stringPattern.matcher(content);
        while (m.find()) {
            String name = m.group(1);
            String text = m.group(2);
            text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&");
            text = text.replace("\\'", "'").replace("\\\"", "\"");
            strings.put(name, text);
        }
        return strings;
    }

    private static String readFile(File file) throws Exception {
        BufferedReader reader = new BufferedReader(new FileReader(file));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) sb.append(line).append("\n");
        reader.close();
        return sb.toString();
    }
}
