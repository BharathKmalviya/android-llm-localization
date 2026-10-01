import java.io.File;
import java.util.*;
import java.util.regex.*;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.*;

/** Java runtime formatting checks; Python checks XML and source parity first. */
public class VerifyStrings {
    private static final Pattern FORMAT = Pattern.compile(
        "%(?:(\\d+)\\$)?([-#+ 0,(<]*)(\\d+)?(?:\\.(\\d+))?([tT][a-zA-Z]|[a-zA-Z%])");
    private static final Pattern LOCALE = Pattern.compile(
        "values-(?:[a-z]{2,3}(?:-r(?:[A-Z]{2}|\\d{3}))?|b\\+[a-z]{2,3}(?:\\+[A-Za-z0-9]{2,8})*)(?:-[A-Za-z0-9]+)*");

    private static class Resource {
        final String text;
        final boolean formatted;
        Resource(Element element, boolean parentFormatted) {
            text = element.getTextContent().replace("\\'", "'").replace("\\\"", "\"");
            formatted = parentFormatted && !"false".equals(element.getAttribute("formatted"));
        }
    }

    public static void main(String[] args) throws Exception {
        File resDir = new File(args.length > 0 ? args[0] : "app/src/main/res");
        if (!resDir.isDirectory()) {
            System.err.println("Fatal: Could not find resource directory: " + resDir);
            System.exit(1);
        }
        Map<String, Resource> source = parse(new File(resDir, "values/strings.xml"));
        File[] locales = resDir.listFiles(file -> file.isDirectory()
            && LOCALE.matcher(file.getName()).matches()
            && !file.getName().split("-")[1].equals("car"));
        int checked = 0, errors = 0;
        if (locales != null) {
            Arrays.sort(locales);
            for (File locale : locales) {
                File file = new File(locale, "strings.xml");
                if (!file.isFile()) continue;
                for (Map.Entry<String, Resource> entry : parse(file).entrySet()) {
                    Resource original = source.get(entry.getKey());
                    Resource translated = entry.getValue();
                    if (original == null || !original.formatted || !translated.formatted) continue;
                    try {
                        Object[] values = arguments(original.text);
                        if (values.length == 0 && !FORMAT.matcher(original.text).find()) continue;
                        String.format(Locale.ROOT, translated.text, values);
                        checked++;
                    } catch (IllegalArgumentException ex) {
                        System.err.println("ERROR: [" + locale.getName() + "] " + entry.getKey()
                            + ": " + ex.getClass().getSimpleName() + " - " + ex.getMessage());
                        errors++;
                    }
                }
            }
        }
        System.out.println("Java formatting: " + checked + " checked, " + errors + " errors.");
        if (errors > 0) System.exit(1);
    }

    private static Object[] arguments(String text) {
        Map<Integer, String> types = new TreeMap<>();
        Matcher matcher = FORMAT.matcher(text);
        int ordinary = 0, previous = 0;
        while (matcher.find()) {
            String conversion = matcher.group(5);
            if (conversion.equals("%") || conversion.equals("n")) continue;
            int index;
            if (matcher.group(2).contains("<")) {
                index = previous;
            } else if (matcher.group(1) != null) {
                index = Integer.parseInt(matcher.group(1));
            } else {
                index = ++ordinary;
            }
            if (index < 1 || index > 10000) {
                throw new IllegalArgumentException("format argument index outside supported range 1..10000");
            }
            previous = index;
            char suffix = Character.toLowerCase(conversion.charAt(conversion.length() - 1));
            String type = conversion.length() == 2 ? "integer"
                : "dox".indexOf(suffix) >= 0 ? "integer"
                : "efga".indexOf(suffix) >= 0 ? "decimal"
                : suffix == 'c' ? "character" : "object";
            if (type.equals("integer") && "character".equals(types.get(index)) && conversion.length() == 1) {
                continue; // Integer supports both %c and integer conversions, regardless of order.
            }
            if (!type.equals("object") || !types.containsKey(index)) types.put(index, type);
        }
        if (types.isEmpty()) return new Object[0];
        Object[] values = new Object[Collections.max(types.keySet())];
        Arrays.fill(values, "test");
        for (Map.Entry<Integer, String> entry : types.entrySet()) {
            Object value;
            switch (entry.getValue()) {
                case "integer": value = 42L; break;
                case "decimal": value = 3.14; break;
                case "character": value = 65; break;
                default: value = "test";
            }
            values[entry.getKey() - 1] = value;
        }
        return values;
    }

    private static Map<String, Resource> parse(File file) throws Exception {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setNamespaceAware(true);
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
        factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
        factory.setXIncludeAware(false);
        factory.setExpandEntityReferences(false);
        Document document = factory.newDocumentBuilder().parse(file);
        Map<String, Resource> resources = new LinkedHashMap<>();
        NodeList nodes = document.getDocumentElement().getChildNodes();
        for (int i = 0; i < nodes.getLength(); i++) {
            if (!(nodes.item(i) instanceof Element)) continue;
            Element element = (Element) nodes.item(i);
            String tag = element.getTagName();
            String key = tag + ":" + element.getAttribute("name");
            boolean formatted = !"false".equals(element.getAttribute("formatted"));
            if (tag.equals("string")) {
                resources.put(key, new Resource(element, formatted));
            } else if (tag.equals("string-array") || tag.equals("plurals")) {
                NodeList children = element.getChildNodes();
                int itemIndex = 0;
                for (int j = 0; j < children.getLength(); j++) {
                    if (!(children.item(j) instanceof Element)) continue;
                    Element item = (Element) children.item(j);
                    if (!item.getTagName().equals("item")) continue;
                    String identity = tag.equals("plurals") ? item.getAttribute("quantity") : "" + itemIndex++;
                    resources.put(key + "[" + identity + "]", new Resource(item, formatted));
                }
            }
        }
        return resources;
    }
}
