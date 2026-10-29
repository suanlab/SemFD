# External baselines (not vendored)

- **FastRFD** (Li et al., PVLDB 18(7) 2025). Clone https://github.com/YukinoMR/FastRFD (commit of 2025-01-26).
  - The upstream `pom.xml` declares no dependencies, so the clone does not build as-is. Replace it with
    `baselines/fastrfd_pom.xml`, which adds RoaringBitmap, fastutil, picocli, koloboke and javacsv, plus a fat-jar assembly.
  - Build with JDK >= 18 (we use Temurin 21) and Maven 3.9: `mvn -DskipTests package`, which produces `target/FastRFD.jar`.
  - `exp/b2_fastrfd.py` finds the jar and Java through the env vars `FASTRFD_JAR` and `FASTRFD_JAVA` (else `~/opt/jdk-21*`, else `java` on `PATH`), resolved at run time; `FASTRFD_XMX` sets the heap (default 200g). A non-zero exit raises, and the full output is saved under `results/icde27/logs/`.
  - The upstream license is unclear: the README says Apache-2.0 but links to another repository's LICENSE. We run it and do not redistribute it.
- **Desbordante** 2.5.0 (`pip install desbordante`, AGPL-3.0). It is called as a library and not vendored.
- FastRFD silently reads only the first 1000 tuples unless `-r -1` is passed (README claims default -1).
- FastRFD's CSV reader splits on every comma and has no quoting (`RelationalInput.java`), so commas inside values are replaced by spaces after Layer-1 normalization; each run records the sha256 of the table and threshold file it was given.
- A rule with an empty left-hand side is printed as ` --> [Y(<=d)]` and makes every X → Y(≤d) non-minimal, so it is not printed; the wrapper counts every candidate X → Y as accepted then (since 2026-10-29; see `literature/prereg_b2_recheck_2026-10-29.md`).
