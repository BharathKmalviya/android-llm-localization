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
            // Try relative to scripts if the absolute/relative failed
            File fallback = new File("../" + resDirPath);
            if (fallback.exists()) {
                resDir = fallback;
            }
        }
        
        if (!resDir.exists()) {
            System.err.println("Fatal: Could not find resource directory at: " + resDirPath);
            System.exit(1);
        }

        File englishDir = new File(resDir, "values");
        File[] valuesDirs = resDir.listFiles((dir, name) -> name.startsWith("values-"));
        
        if (valuesDirs == null || valuesDirs.length == 0) {
            System.err.println("No values- localized directories found!");
            return;
        }

        System.out.println("Started Android String Format Verification...");
        System.out.println("Scanning source strings in: " + englishDir.getPath());

        // 1. First parse the English strings to know the expected format arguments
        Map<String, String> englishStrings = parseStringsFile(new File(englishDir, "strings.xml"));
        Map<String, List<String>> expectedFormats = new HashMap<>();
        
        // Regex for Android / Java format specifiers
        Pattern formatPattern = Pattern.compile("%(\\d+\\$)?([-#+ 0,(<]*)?(\\d+)?(\\.\\d+)?([tT]?[a-zA-Z%])");
        for (Map.Entry<String, String> entry : englishStrings.entrySet()) {
            List<String> formats = new ArrayList<>();
            Matcher m = formatPattern.matcher(entry.getValue());
            while (m.find()) {
                formats.add(m.group());
            }
            expectedFormats.put(entry.getKey(), formats);
        }

        int totalErrors = 0;
        int totalStringsVerified = 0;

        // 2. Now verify every language against Android String formatting rules
        for (File dir : valuesDirs) {
            File stringsFile = new File(dir, "strings.xml");
            if (!stringsFile.exists()) continue;

            Map<String, String> localizedStrings = parseStringsFile(stringsFile);
            
            for (Map.Entry<String, String> entry : localizedStrings.entrySet()) {
                String name = entry.getKey();
                String text = entry.getValue();
                totalStringsVerified++;

                List<String> englishFormats = expectedFormats.get(name);
                if (englishFormats == null || englishFormats.isEmpty()) {
                    // This string shouldn't have any format arguments.
                    // If it has a %, it must be %%
                    if (text.contains("%") && !text.matches("^(?:[^%]|%%)*$")) {
                        System.err.println("ERROR: [" + dir.getName() + "] String '" + name + "' contains unescaped % but English doesn't use formatting.");
                        System.err.println("  Text: " + text);
                        totalErrors++;
                    }
                    continue;
                }

                // Try to format it via java natively
                try {
                    // Provide generic arguments to satisfy any index like %1$s, %1$d.
                    // Our app primarily uses integers and strings up to 3 parameters.
                    String.format(text, 100, "test_string", 50);
                } catch (UnknownFormatConversionException e) {
                    System.err.println("CRASH: [" + dir.getName() + "] String '" + name + "' has an invalid conversion specifier: " + e.getConversion());
                    System.err.println("  Text: " + text);
                    totalErrors++;
                } catch (MissingFormatArgumentException e) {
                    System.err.println("CRASH: [" + dir.getName() + "] String '" + name + "' is missing format arguments or index is wrong: " + e.getFormatSpecifier());
                    System.err.println("  Text: " + text);
                    totalErrors++;
                } catch (IllegalFormatConversionException e) {
                    System.err.println("CRASH: [" + dir.getName() + "] String '" + name + "' uses wrong variable type logic (e.g. used %d instead of %s): " + e.getMessage());
                    System.err.println("  Text: " + text);
                    System.err.println("  English expected: " + englishStrings.get(name));
                    totalErrors++;
                } catch (Exception e) {
                    System.err.println("CRASH: [" + dir.getName() + "] String '" + name + "' failed native String.format() -> " + e.getClass().getSimpleName() + ": " + e.getMessage());
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

    private static Map<String, String> parseStringsFile(File file) throws Exception {
        Map<String, String> strings = new HashMap<>();
        BufferedReader reader = new BufferedReader(new FileReader(file));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            sb.append(line).append("\n");
        }
        reader.close();

        // This regex ensures we only grab actual text contents inside `<string>`
        Pattern stringPattern = Pattern.compile("<string name=\"([^\"]+)\"[^>]*>(.*?)</string>", Pattern.DOTALL);
        Matcher m = stringPattern.matcher(sb.toString());
        while (m.find()) {
            String name = m.group(1);
            String text = m.group(2);
            // Decode standard XML entity things that AAPT2 does automatically
            text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&");
            // Unescape apostrophes and quotes as Java expects clean strings
            text = text.replace("\\'", "'").replace("\\\"", "\"");
            strings.put(name, text);
        }
        return strings;
    }
}
