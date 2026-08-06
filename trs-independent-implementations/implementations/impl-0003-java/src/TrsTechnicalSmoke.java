import java.util.*;
public final class TrsTechnicalSmoke {
  static boolean validate(String id, String type, List<String> causes, Set<String> known) { return !id.isEmpty() && Set.of("Observation","Commitment","Intention").contains(type) && (causes.isEmpty() || known.containsAll(causes)); }
  public static void main(String[] args) { if (!validate("g1","Observation",List.of(),Set.of())) throw new AssertionError(); System.out.println("TRS Java technical smoke pass"); }
}
