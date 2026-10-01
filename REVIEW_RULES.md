# VTK review rules (draft)

Drafted automatically from VTK merge request reviews before 2026-10-01. Each rule groups conventions that reviewers stated in their own words across several merge requests (cosine distance 0.25). Nothing here is approved: a maintainer should accept, edit, merge, or reject each rule.

Every supporting comment was checked individually against the stated rule; comments about something else were removed from the support counts, and comments that disagree are listed as counter-evidence. A rule marked *mixed evidence* has at least one counter-example.

## style

### R003: Use `this->` prefix for member variable and method access within class methods.

- Scope: C++ source files
- Support: 27 MRs, 40 threads, 2017-01-26 to 2025-03-13
- Reviewers: jpouderoux (9), cory.quammen (5), charles.gueunet (5), mwestphal (3), michael.migliore (3)
- [!11971](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11971) acbauer, 2025-03-13: "Use `this->` for class members"
- [!11347](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11347) lucas.givord, 2024-07-24: "don't forget `this->` before using a class method (same remark for below)"
- [!9663](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9663) ben.boeckel, 2022-11-02: "Please use `this->` for all member accesses."

### R004: Use camelCase for variable names.

*Mixed evidence: check the examples before accepting.*

- Scope: local variables and general variables in C++ code
- Support: 26 MRs, 29 threads, 2015-06-28 to 2026-09-10
- Reviewers: jpouderoux (5), cory.quammen (5), mwestphal (5), utkarsh.ayachit (2), charles.gueunet (2)
- [!13296](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13296) lucas.gottar, 2026-06-01: "local variables should be camel case no ?"
- [!12688](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12688) michael.migliore, 2025-12-09: "`Timestamp` is a single word so `S` should be lowercase."
- [!11449](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11449) charles.gueunet, 2024-09-02: "please, avoid starting a local variable with an uppercase, as this is reserved for class fields."
- Counter-evidence:
  - [!5334](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5334) lassoan, 2019-03-25: "it is not a class member, make it lowercase (texCoordsFaceAvailable)"
  - [!7483](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7483) ben.boeckel, 2021-01-13: "For local variables, please use lowercase. Something like `vtk_supported_qt_versions`."
  - [!8329](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8329) charles.gueunet, 2021-08-24: "Naming: prefer lower case for the first letter of a local variable (here and after)"

### R007: Place local functions, variables, and structs in an anonymous namespace.

*Mixed evidence: check the examples before accepting.*

Rationale: to ensure uniqueness to the compilation unit

- Scope: C++ sources
- Support: 20 MRs, 23 threads, 2015-11-23 to 2026-08-25
- Reviewers: lucas.givord (7), yohann.bearzi (3), mwestphal (2), julien.fausty (2), thomas.galland (2)
- [!13356](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13356) dcthomp, 2026-06-19: "1. Put local functions in an anoymous namespace instead of declaring them static."
- [!12311](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12311) lucas.givord, 2025-10-28: "should be in the anonymous namespace"
- [!12185](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12185) mathurin.lemarie, 2025-07-01: "This should be in an anonymous namespace"
- Counter-evidence:
  - [!11711](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11711) mwestphal, 2024-12-02: "use `::` then"
  - [!11824](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11824) sankhesh, 2025-01-15: "Could we please avoid anonymous namespace here? IMHO, these functions can be in a named vtkanari-specific namespace`."

### R008: Use C++-style casts (static_cast or reinterpret_cast) instead of C-style casts.

Rationale: C++-style casts improve code clarity and safety; constness should not be cast away without good reason, and older C-style casts in legacy code should be updated.

- Scope: C++ code
- Support: 19 MRs, 19 threads, 2018-12-13 to 2026-07-21
- Reviewers: mwestphal (3), alliepiper16 (2), michael.migliore (2), yohann.bearzi (2), demarle (1)
- [!13472](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13472) jaswant.panchumarti, 2026-07-21: "Use C++ style cast ```suggestion:-0+0 const long* extents = reinterpret_cast<const long*>(data); // left, right, top, bottom ```"
- [!9207](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9207) timothee.chabat, 2022-05-23: "prefer static_cast over C cast"
- [!8884](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8884) seanm, 2022-02-04: "Should probably be `static_cast<vtkIdType>` now I think..."

### R009: Use nullptr instead of 0, NULL, or other null pointer constants for pointer initialization and comparison.

*Mixed evidence: check the examples before accepting.*

- Scope: all C++ code
- Support: 18 MRs, 21 threads, 2017-06-13 to 2026-01-19
- Reviewers: ben.boeckel (5), cory.quammen (4), mwestphal (4), yohann.bearzi (2), robertmaynard (1)
- [!12021](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12021) mwestphal, 2025-03-28: "double* ShapeFunctionDerivativeWeights = nullptr;"
- [!11842](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11842) mwestphal, 2025-01-15: "vtkMultiProcessController* Controller = nullptr;"
- [!9519](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9519) ben.boeckel, 2022-09-01: "Please use `nullptr` instead of `NULL` in all C++ code."
- Counter-evidence:
  - [!1485](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1485) utkarsh.ayachit, 2016-05-12: "use `NULL` we so can grep-replace to `nullptr` when time comes."

### R010: Use braces {} for all if, for, and while statements in VTK code.

- Scope: C++ source code
- Support: 18 MRs, 19 threads, 2015-09-10 to 2024-09-23
- Reviewers: dgobbi (4), ken-martin (4), cory.quammen (3), demarle (2), ben.boeckel (1)
- [!11506](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11506) dgobbi, 2024-09-23: "VTK code style includes `this` on method calls, and braces on if/for/while: ```c++ if (!this->EnsureGenericDisplay()) { return nullptr; } ```"
- [!11361](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11361) leon.victor, 2024-08-13: "vtk style enforces braces for all for loops"
- [!7521](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7521) cory.quammen, 2023-03-24: "VTK style requires braces {} for any conditional section."

### R011: Use `bool` instead of `vtkTypeBool` for new or refactored boolean member variables and their setters/getters where macros allow it.

*Mixed evidence: check the examples before accepting.*

Rationale: `vtkTypeBool` is the old style and has been deprecated; `bool` is the modern C++ type and is recommended for new code.

- Scope: new or refactored members where macros allow it
- Support: 17 MRs, 19 threads, 2018-11-29 to 2026-09-29
- Reviewers: mwestphal (4), utkarsh.ayachit (3), cory.quammen (3), jpouderoux (2), borisb (1)
- [!13687](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13687) mwestphal, 2026-09-29: "Why not also change from `vtkTypeBool Cppaing` to `bool Capping`? Retrocompatibility because of the set/get macros?"
- [!12975](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12975) cory.quammen, 2026-03-17: "Make this a bool (if appropriate), add `vtkBooleanMacro`."
- [!12984](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12984) mwestphal, 2026-03-05: "vtkSetMacro(UseImplicitArray, bool); vtkBooleanMacro(UseImplicitArray, bool)"
- Counter-evidence:
  - [!1171](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1171) cory.quammen, 2016-02-03: "With respect to this change, I would recommend defining the VTK bool type format defined in Common/Core/vtkType.h and name the bool type vtkTypeBool. More verbose, yes, but it is at least consistent w"
  - [!1171](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1171) lorensen, 2016-07-08: "I agree with Cory that the new type should be vtkTypeBool to be consistent with most of the types in vtkType.h"
  - [!8314](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8314) tiffany.chhim, 2021-08-20: "vtkTypeBool is actually deprecated, bool can always be used."

### R012: Always use curly braces {} for if, else, for, and while blocks, even when the body is a single statement.

- Scope: C++ sources
- Support: 17 MRs, 17 threads, 2016-01-12 to 2026-02-06
- Reviewers: mwestphal (2), lorensen (2), jpouderoux (2), michael.migliore (2), sebastienbarre (1)
- [!7806](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7806) cory.quammen, 2021-04-02: "Curly braces needed for both true and false branches."
- [!7039](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7039) utkarsh.ayachit, 2020-06-22: "minor style: use `{}` after `if`."
- [!6782](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6782) ben.boeckel, 2020-04-21: "They are required by style, but not present everywhere in VTK."

### R013: Use vtkIdType for loop counters, indices, and variables related to point or cell counts and IDs.

*Mixed evidence: check the examples before accepting.*

- Scope: C++ sources
- Support: 17 MRs, 21 threads, 2017-01-18 to 2026-05-06
- Reviewers: christos.tsolakis (4), jpouderoux (3), mwestphal (2), timothee.chabat (2), lucas.givord (2)
- [!13098](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13098) mwestphal, 2026-05-06: "-0+0 //------------------------------------------------------------------------------ vtkIdType vtkJumpAndWalkCellLocator::FindCellWalk(vtkIdList* cellIds, double x[3], double tol2,"
- [!12420](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12420) lucas.givord, 2025-10-10: "vtkIdType instead of int"
- [!11305](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11305) will.schroeder, 2024-07-09: "The problem is with what kind of variable do you initialize it with, if it was ```auto i = this->NumberOfPoints``` it would work, ```auto i = 0``` does not work because 0 is an int."
- Counter-evidence:
  - [!6621](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6621) utkarsh.ayachit, 2020-04-13: "this should raise a warning. `GetNumberOfValues` returns a `vtkIdType`, if I am not mistaken. use ` return static_cast<int>(this->TimeDataStringArray->GetNumberOfValues()); `"

### R014: Use VTK logging macros (e.g., vtkLog, vtkWarningMacro, vtkErrorMacro, vtkGenericWarningMacro, vtkDebugWithObjectMacro) instead of standard C++ streams (std::cout, std::cerr) or C-style I/O (fprintf, cout) for logging.

Rationale: VTK logging macros enable easier error capture in applications and ensure consistency with VTK's logging infrastructure.

- Scope: all C++ sources
- Support: 17 MRs, 17 threads, 2016-10-26 to 2026-06-24
- Reviewers: mwestphal (5), utkarsh.ayachit (2), cory.quammen (2), ben.boeckel (2), lorensen (1)
- [!13365](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13365) lucas.givord, 2026-06-24: "we should use vtkLog here too"
- [!13052](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13052) mwestphal, 2026-04-02: "function 'fprintf' is unsafe and slow; 'vtk::print or vtk::println' should be used instead"
- [!12321](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12321) spiros.tsalikis, 2025-12-10: "replace std::cerr everywhere with vtkLogF like you do below"

### R015: Avoid single-letter variable names.

- Scope: unspecified
- Support: 17 MRs, 19 threads, 2021-08-13 to 2026-07-09
- Reviewers: mwestphal (14), lucas.givord (3), thomas.galland (2)
- [!13429](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13429) lucas.givord, 2026-07-09: "avoid one letter variable name, we should rename it "state" I believe"
- [!12699](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12699) lucas.givord, 2025-12-09: "Generally, we should avoid using one letter for variable naming, could you please change that for `v`, `m` ?"
- [!12611](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12611) mwestphal, 2025-11-18: "avoid single letter var"

### R016: Member variables should be private.

*Mixed evidence: check the examples before accepting.*

- Scope: C++ class definitions
- Support: 15 MRs, 15 threads, 2019-02-15 to 2026-06-11
- Reviewers: mwestphal (12), ben.boeckel (1), nicolas.vuaille (1), spiros.tsalikis (1)
- [!12764](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12764) spiros.tsalikis, 2026-01-26: "These need to be private members."
- [!12611](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12611) mwestphal, 2025-11-13: "every menbers should be private"
- [!12311](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12311) mwestphal, 2025-10-21: "I am moving it to the private section"
- Counter-evidence:
  - [!5377](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5377) jpouderoux, 2019-05-03: "Why are these members private and not protected? They should have been protected. I'm changing that in the reader as well."

### R018: Use camelCase for method names in VTK C++ code, with the first letter capitalized (PascalCase for method names).

*Mixed evidence: check the examples before accepting.*

- Scope: C++ method names
- Support: 13 MRs, 13 threads, 2015-05-01 to 2026-07-01
- Reviewers: cory.quammen (5), dgobbi (2), lucas.givord (2), aashish-chaudhary (1), LucasGandelKitware (1)
- [!13373](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13373) jaswant.panchumarti, 2026-07-01: "drop `_`? the rationale being we do not mix `snake_case` and `CamelCase` in VTK's C++. ```suggestion:-1+0 std::atomic<unsigned int> gRefCount{ 0 }; vtkInformationKeyLookupKeysType* gKeys = nullptr; ``"
- [!12655](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12655) mwestphal, 2025-11-27: "is_success does not follow vtk guidelines to use camelCase"
- [!11725](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11725) lucas.givord, 2024-12-04: "you probably do too much python recently so that you use using snake_case variable in vtk, we should avoid that"
- Counter-evidence:
  - [!11971](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11971) acbauer, 2025-03-13: "Would prefer that all class member variables start with capital letter for VTK code formatting consistency"

### R020: Remove commented-out code.

- Scope: unspecified
- Support: 13 MRs, 14 threads, 2017-02-21 to 2025-09-01
- Reviewers: mwestphal (3), tjcorona (2), ben.boeckel (1), demarle (1), jpouderoux (1)
- [!11708](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11708) thomas.galland, 2024-12-16: "here and bellow: remove commented code"
- [!10397](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10397) nicolas.vuaille, 2023-08-09: "Why this info ? Is there another way to setup the filter? Right, I'll remove it as there are no other way to add values to vectors"
- [!9812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9812) julien.fausty, 2023-04-20: "Please remove commented code"

### R023: Use the 'override' keyword instead of 'virtual' for member functions that override a base class virtual function.

- Scope: C++ source files
- Support: 12 MRs, 15 threads, 2018-02-12 to 2024-06-18
- Reviewers: mwestphal (7), jpouderoux (2), robertmaynard (2), michael.migliore (1), charles.gueunet (1)
- [!10981](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10981) mwestphal, 2024-03-22: "virtual should not be here at the same time as override (true in the whole file btw)"
- [!10324](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10324) ben.boeckel, 2023-07-08: "`virtual override` is redundant. `clang-tidy` points this out"
- [!8475](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8475) mwestphal, 2021-12-19: "'GetActors' overrides a member function but is not marked 'override'"

### R024: Initialize member variables in the constructor initializer list.

- Scope: C++ constructors
- Support: 12 MRs, 12 threads, 2019-05-07 to 2025-09-24
- Reviewers: mwestphal (3), sebastien.jourdain (1), florian.chevassu (1), yohann.bearzi (1), nicolas.vuaille (1)
- [!11844](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11844) mwestphal, 2025-01-17: "you can init the value here. ```suggestion:-0+0 bool EnableTouchEventProcessing = true; ```"
- [!10223](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10223) thomas.galland, 2023-05-24: "Here and bellow: : `this->TranslationAxis = Axis::NONE` -> `: Axis::NONE` ? (seems you are double assigning here, or I misunderstand something)"
- [!9193](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9193) timothee.chabat, 2022-05-18: "you can just add `, CustomSubdivisions(2, 2)` to the class initializer list"

### R026: Use range-based for loops instead of index-based or iterator-based loops when iterating over containers.

- Scope: C++ sources
- Support: 12 MRs, 19 threads, 2019-08-01 to 2025-11-18
- Reviewers: utkarsh.ayachit (4), mwestphal (3), mzeyen (2), spiros.tsalikis (2), charly.bollinger (2)
- [!12611](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12611) mwestphal, 2025-11-18: "-0+0 for (vtkLineRepresentation* lineRepresentation : LineRepresentationVector)"
- [!10587](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10587) charly.bollinger, 2023-10-12: "for (const auto& block : blocks) iterator loop here and below? unless you explicitly need the index"
- [!9812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9812) spiros.tsalikis, 2023-05-15: "change the for loop to ```for (const auto& cellPoint : cellPointSet) { cellArray->InsertCellPoint(cellPoint); }```"

### R027: In a PrintSelf method, call this->Superclass::PrintSelf(os, indent) first, then print all member variables of the class, including calling PrintSelf recursively on internal vtk class members, and do not call methods with side effects.

- Scope: C++ source files implementing vtkObject subclasses
- Support: 11 MRs, 11 threads, 2015-07-14 to 2024-11-13
- Reviewers: mwestphal (3), utkarsh.ayachit (2), tiffany.chhim (1), christos.tsolakis (1), jcfr (1)
- [!11165](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11165) thomas.galland, 2024-05-29: "For internal members being vtk classes, I think you could call `Printself` on them recursively"
- [!10302](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10302) lucas.givord, 2023-07-18: "the `Superclass::PrintSelf` should be the first print called in this method"
- [!10227](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10227) charly.bollinger, 2023-06-06: "Seems VTK classes should always override the PrintSelf method (this is one of the `header checks` done in the CI), even if there is nothing more to print. I think this is done in order to not forget t"

### R029: Sort includes alphabetically.

- Scope: C++ source files
- Support: 11 MRs, 12 threads, 2016-12-05 to 2026-09-28
- Reviewers: mwestphal (6), demarle (3), alouis (2), mzeyen (1)
- [!13052](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13052) mwestphal, 2026-03-23: "Also keep it sorted."
- [!5824](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5824) mzeyen, 2019-08-19: "Includes are not ordered alphabetically"
- [!2937](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2937) alouis, 2017-06-19: "Please sort includes by alphabetical order"

### R030: Use 'this->' prefix for all member variable and method access within class implementations in VTK C++ code.

- Scope: C++ source files (class implementations)
- Support: 11 MRs, 11 threads, 2017-09-18 to 2025-11-19
- Reviewers: cory.quammen (3), demarle (2), mwestphal (2), dgobbi (1), sujin.philip (1)
- [!11247](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11247) cory.quammen, 2024-07-12: "Use `this->` per VTK style guidelines."
- [!8405](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8405) cory.quammen, 2021-09-17: "VTK style - prefix internal member access with `this->`"
- [!7247](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7247) yohann.bearzi, 2020-09-21: "Every attributes of the class should have `this->` suffix to match VTK's code practices."

### R032: Initialize member variables directly in the header file.

*Mixed evidence: check the examples before accepting.*

Rationale: Modernization is more important than consistency; initializing in the header improves clarity and reduces boilerplate in constructors.

- Scope: C++ header files (for member variable declarations)
- Support: 10 MRs, 10 threads, 2019-05-28 to 2026-04-07
- Reviewers: mwestphal (8), timothee.chabat (1), guillaume.gisbert (1)
- [!13113](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13113) mwestphal, 2026-04-07: "We usually prefer initialisation in header. Feel free to update all the members if you want."
- [!12611](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12611) guillaume.gisbert, 2025-11-18: "init in header same with this->WidgetState"
- [!12459](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12459) mwestphal, 2025-09-29: "lets initi this in the header too :smile:"
- Counter-evidence:
  - [!8470](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8470) mwestphal, 2021-10-18: "I don't see many (or maybe any?) cases where we initialize member variables using _SafeDownCast_ in the header, so my feeling is initialization should remain in the source file."

### R034: Use std::size_t instead of size_t.

*Mixed evidence: check the examples before accepting.*

Rationale: To always put the namespace, avoiding ambiguity and ensuring portability.

- Scope: C++ sources
- Support: 9 MRs, 12 threads, 2018-05-02 to 2025-05-06
- Reviewers: lucas.givord (6), cory.quammen (2), jaswant.panchumarti (2), jpouderoux (1), mwestphal (1)
- [!12088](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12088) lucas.givord, 2025-05-06: "we should always put the namespace, so in this case we need to change `size_t` to `std::size_t`"
- [!11986](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11986) mwestphal, 2025-03-28: "please check every use"
- [!11380](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11380) lucas.givord, 2024-08-09: "use std::size_t (here and everywhere)"
- Counter-evidence:
  - [!8051](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8051) dgobbi, 2021-06-09: "You can declare `i` and `listSize` as `size_t` to avoid compiler warnings."

### R041: Use const std::string& for string parameters and std::string instead of raw const char* for strings to avoid conversions, nullptr checks, and unnecessary copies.

*Mixed evidence: check the examples before accepting.*

Rationale: to avoid conversions, nullptr checks, and unnecessary copies

- Scope: C++ sources
- Support: 8 MRs, 11 threads, 2019-05-06 to 2025-12-09
- Reviewers: mwestphal (5), michael.migliore (2), cory.quammen (1), charles.gueunet (1), louis.gombert (1)
- [!11129](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11129) louis.gombert, 2024-05-30: "working with only `std::string` here and in the function below would be easier and avoid conversions"
- [!9346](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9346) charles.gueunet, 2022-07-05: "may you use a string ? this would avoid the need to check agains `nullptr` each time."
- [!8503](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8503) mwestphal, 2021-10-08: "you can use std::string (and the adequate macro)"
- Counter-evidence:
  - [!5096](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5096) ken-martin, 2019-01-28: "As uniform calls can happen a lot in the inner loop that can be a bottleneck. In this MR https://gitlab.kitware.com/vtk/vtk/merge_requests/1898/diffs I switched from std::string to const char * and ou"
  - [!8535](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8535) cory.quammen, 2021-10-19: "The `std::string` doesn't seem necessary here as you are using it's `c_str()` function to access a character string - just use the raw character string from `this->GetInputArrayInformation(0)->Get(vtk"

### R043: Use vtkSetClampMacro for integer setters with min/max bounds, including enum values and bounded integer parameters.

- Scope: C++ source code (class member setters)
- Support: 8 MRs, 10 threads, 2015-06-29 to 2026-08-17
- Reviewers: utkarsh.ayachit (4), acbauer (2), jpouderoux (1), tiffany.chhim (1), nicolas.vuaille (1)
- [!12500](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12500) nicolas.vuaille, 2025-10-07: "I follow what the macro do previously (define a virtual setter, getter for min, getter for max), because I need to forward the BoundaryMode set by the user internally"
- [!9179](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9179) tiffany.chhim, 2022-05-12: "vtkSetClampMacro(VectorScaleMode, int, SCALE_BY_MAGNITUDE, SCALE_BY_COMPONENTS); vtkGetMacro(VectorScaleMode, int);"
- [!8408](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8408) utkarsh.ayachit, 2021-09-13: "please the enum for range. `vtkSetClampMacro(Mode, int, vtkPartitionBalancer::Expand, vtkPartitionBalancer::Squash`."

### R044: Remove extra empty lines to leave only one empty line between sections.

- Scope: unspecified
- Support: 8 MRs, 9 threads, 2017-10-02 to 2025-05-23
- Reviewers: mwestphal (4), michael.migliore (2), LucasGandelKitware (1), jcfr (1), nicolas.vuaille (1)
- [!12107](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12107) mwestphal, 2025-05-23: "lets remove the supplementary empty lines ?"
- [!10164](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10164) jcfr, 2023-05-01: "Only have one empty line"
- [!4909](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4909) michael.migliore, 2018-11-22: "remove two extra empty lines"

### R045: Use vtkSetMacro and vtkGetMacro (or vtkGetObjectMacro/vtkCxxSetObjectMacro for object pointers) for property accessors in VTK classes.

Rationale: When not using macros for a setter/getter, you are saying to other VTK dev that these setter/getter are special and requires something special. They do not here.

- Scope: C++ sources (specifically vtkObject subclasses and Python-wrapping modules)
- Support: 8 MRs, 8 threads, 2018-03-28 to 2025-04-04
- Reviewers: jpouderoux (2), utkarsh.ayachit (2), michael.migliore (1), mwestphal (1), julia.sanchez (1)
- [!11988](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11988) lucas.givord, 2025-04-04: "we use a vtk macro for this one"
- [!10017](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10017) julia.sanchez, 2023-03-01: "vtkSetMacro(SearchMode, NeighborSearchMode); vtkGetMacro(SearchMode, NeighborSearchMode);"
- [!7994](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7994) utkarsh.ayachit, 2021-05-21: "VTK style for such methods is as follows: ```c++ // in .h void SetParmetricFunction(vtkParametricFunction*); vtkGetObjectMacro(ParametricFunction, vtkParametricFunction); ... vtkParametricFunction* Pa"

### R046: Use `= default` for special member functions instead of empty bodies.

- Scope: C++ class definitions (specifically for special member functions such as constructors, destructors, etc.)
- Support: 8 MRs, 9 threads, 2018-04-03 to 2025-12-08
- Reviewers: mwestphal (3), ben.boeckel (2), jpouderoux (1), sujin.philip (1), michael.migliore (1)
- [!9487](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9487) ben.boeckel, 2022-09-01: "`clang-tidy` will want this (and other things) to be `= default`."
- [!7753](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7753) ben.boeckel, 2021-03-16: "`= default`. I'll leave the `clang-tidy` CI job to find anything else like this."
- [!6212](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6212) michael.migliore, 2019-11-20: "remove this line and use `= default` in the header"

### R047: Use double quotes for VTK headers (e.g., "vtkClass.h") instead of angle brackets.

*Mixed evidence: check the examples before accepting.*

- Scope: VTK headers
- Support: 7 MRs, 7 threads, 2015-10-12 to 2025-03-03
- Reviewers: yohann.bearzi (2), cory.quammen (1), demarle (1), mwestphal (1), ben.boeckel (1)
- [!8054](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8054) ben.boeckel, 2021-06-07: "Why is this using `<>` and not `""` like all of the other VTK headers?"
- [!5930](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5930) mwestphal, 2021-04-20: "Each include in VTK needs a justification, something like this: #include "vtkContextItem.h" #include "vtkInteractionWidgetsModule.h" // Needed for bla #include "vtkNew.h" // Needed for vtkNew #include"
- [!7213](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7213) yohann.bearzi, 2020-09-04: "The convention is to use "vtkSomething.h" instead of <vtkSomething.h>. Same remark goes for the test."
- Counter-evidence:
  - [!4112](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4112) aashish-chaudhary, 2018-03-27: "just to be consistent you want to use < brackets and not ""
  - [!6301](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6301) todoooo, 2019-12-20: "It means that VTK headers are not allowed to include "vtksys/FStream.hxx"."

### R051: Use std::array instead of C-style arrays for fixed-size collections known at compile time.

Rationale: It simplifies algorithms (e.g., computing table length, looping over indices without nullptr checks) and is preferred for static sizes.

- Scope: C++ source code (implied by use of std::array and C-style arrays in code reviews)
- Support: 7 MRs, 7 threads, 2021-06-07 to 2026-04-10
- Reviewers: timothee.chabat (2), ben.boeckel (1), charles.gueunet (1), leon.victor (1), guillaume.gisbert (1)
- [!13117](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13117) lucas.givord, 2026-04-10: "we can use an std::array , same for CellAttribLabels uses std::array now"
- [!12455](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12455) guillaume.gisbert, 2025-09-29: "i feel like it could be replaced with a std::array. This could simplify some algorithms like GetClassNameFromTypeId when computing table length, or looping over indices and not comparing to nullptr"
- [!11358](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11358) leon.victor, 2024-08-02: "If the size is static use an `std::array`"

### R053: Follow VTK style guidelines, including using `//--------------------------------------------------------------------------` between functions, placing braces on new lines, using spaces after commas in function calls, and avoiding unnecessary `std::` namespace qualifiers for `endl`.

Rationale: To maintain consistency with the rest of VTK code and adhere to the official VTK style guide.

- Scope: C++ sources
- Support: 7 MRs, 7 threads, 2016-07-18 to 2020-03-20
- Reviewers: jpouderoux (2), will.schroeder (1), utkarsh.ayachit (1), demarle (1), alliepiper16 (1)
- [!6604](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6604) finetjul, 2020-03-20: "VTK standard is : `//--------------------------------------------------------------------------`. I will add it."
- [!4909](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4909) jpouderoux, 2018-11-21: "there are still plenty of { at the end of a line of code. Please respect VTK style."
- [!4694](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4694) demarle, 2018-10-03: "Prefer {}'s per vtk style guide. See section 3 item 9 of https://www.vtk.org/wp-content/uploads/2017/06/TheVTKSoftwareProcess.pdf"

### R057: Use `bool` instead of `int` for boolean variables and set/get methods.

- Scope: C++ code
- Support: 7 MRs, 13 threads, 2017-08-18 to 2026-03-17
- Reviewers: christos.tsolakis (6), cory.quammen (4), timothee.chabat (2), jpouderoux (1)
- [!9626](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9626) christos.tsolakis, 2022-11-08: "`bool abort = false;`"
- [!9531](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9531) christos.tsolakis, 2022-09-19: "should be `bool abort = false`."
- [!9270](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9270) christos.tsolakis, 2022-08-04: "same here , replace `int` with `bool`"

### R058: Use explicit type declarations instead of `auto` when the type is not obvious from the expression or context.

Rationale: Because `auto` obscures the type of the object, requiring developers to navigate to the function returning the object to figure it out, and leaving developers wondering what the actual type is when it is not visible elsewhere.

- Scope: C++ sources
- Support: 7 MRs, 7 threads, 2021-02-16 to 2026-05-06
- Reviewers: charles.gueunet (3), mwestphal (2), LucasGandelKitware (1), scott.wittenburg (1)
- [!13098](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13098) mwestphal, 2026-05-06: "avoid using auto when the type is not clear"
- [!10948](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10948) charles.gueunet, 2024-03-12: "I find better to have the exact type on the left side when not already explicit on the right side of the expression"
- [!9636](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9636) scott.wittenburg, 2022-10-20: "I agree, many times auto obscures the type of the object - you need to navigate to the function returning the object to figure this out. I try to only use auto for iterators but sometimes I may slip a"

### R059: Use lowercase for boolean parameter and variable names, and avoid suffixes like 'Active' or 'Enabling'; prefer 'enabled' over 'enabling', and use prefixes like 'HAS_' or 'USE_' for flags to clarify their boolean nature.

*Mixed evidence: check the examples before accepting.*

- Scope: C++ sources
- Support: 6 MRs, 6 threads, 2018-05-31 to 2024-03-07
- Reviewers: LucasGandelKitware (1), mwestphal (1), dgobbi (1), timothee.chabat (1), thomas.galland (1)
- [!10914](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10914) charles.gueunet, 2024-03-07: "`UseCache` switch to `useCache`, uppercase is for internal fields"
- [!10223](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10223) thomas.galland, 2023-05-23: "`enabling` -> enable ? It's just for readability, so that we get more easily the difference when reading `if (enabling && !enabled)`. Not sure we need to rename the parameter`"
- [!9567](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9567) timothee.chabat, 2022-09-26: "I don't think boolean properties needs `Active` at the end since it's already pretty much self explenatory (-> `warp->SideWallsOn()` for example)."
- Counter-evidence:
  - [!3539](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3539) jpouderoux, 2017-11-07: "'highlight' is a whole word, so rename to `HighlightPlot`."

### R060: Initialize pointers to nullptr

*Mixed evidence: check the examples before accepting.*

Rationale: to prevent invalid delete of uninitialized pointer

- Scope: C++ source code (specifically pointer and non-static data member declarations)
- Support: 6 MRs, 6 threads, 2017-12-14 to 2024-08-01
- Reviewers: utkarsh.ayachit (1), nicolas.vuaille (1), mwestphal (1), cory.quammen (1), lucas.givord (1)
- [!11330](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11330) louis.gombert, 2024-08-01: "you can init to `nullptr` here directly"
- [!11271](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11271) lucas.givord, 2024-07-05: "init pointer to nullptr here and below"
- [!5930](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5930) mwestphal, 2021-03-22: "In any case, this should read at least: `vtkContextTransform* Transform = nullptr;`"
- Counter-evidence:
  - [!10914](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10914) nicolas.vuaille, 2024-03-11: "should probably not default to nullptr. Same for other arg"
  - [!13678](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13678) louis.gombert, 2026-09-17: "nullptr initialization is not needed"
  - [!13678](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13678) louis.gombert, 2026-09-17: "nullptr not needed"

### R061: Use spaces around operators.

- Scope: CMake code
- Support: 6 MRs, 6 threads, 2016-12-06 to 2025-11-25
- Reviewers: mwestphal (2), jpouderoux (1), dgobbi (1), jcfr (1), ben.boeckel (1)
- [!12526](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12526) ben.boeckel, 2025-11-25: "foreach (comp IN LISTS VTK_AVAILABLE_COMPONENTS) if(comp IN_LIST skipped_components) continue () endif () if (NOT VTK_${comp}_FOUND) message (SEND_ERROR "Expected VTK component \"${comp}\" could not b"
- [!4087](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4087) jcfr, 2018-03-20: "Consistently use spaces: `i=-baseCube` or `i = -baseCube`"
- [!3647](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3647) mwestphal, 2018-01-08: "spaces, here and everywhere"

### R062: Use EXIT_SUCCESS or EXIT_FAILURE instead of integer literals (0, 1) or boolean values (true, false) as return values in main functions.

- Scope: main functions
- Support: 6 MRs, 6 threads, 2016-12-16 to 2023-10-06
- Reviewers: ben.boeckel (2), lorensen (1), utkarsh.ayachit (1), julien.fausty (1), charly.bollinger (1)
- [!10567](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10567) charly.bollinger, 2023-10-06: "here and below, `return EXIT_FAILURE` instead of `false`"
- [!10501](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10501) julien.fausty, 2023-09-12: "prefer EXIT_SUCCESS/EXIT_FAILURE for explicitness"
- [!10081](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10081) ben.boeckel, 2023-04-24: "Please use `EXIT_FAILURE` and `EXIT_SUCCESS` here."

### R070: Use std::min/max or vtkMath::Min/Max instead of custom implementations or macros.

Rationale: To avoid MSVC 2013 compatibility issues and code generation problems, and for consistency with the codebase.

- Scope: C++ sources
- Support: 6 MRs, 6 threads, 2018-04-30 to 2026-07-02
- Reviewers: cory.quammen (2), utkarsh.ayachit (1), lorensen (1), spiros.tsalikis (1), lucas.givord (1)
- [!11363](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11363) spiros.tsalikis, 2024-09-04: "WHy not just use vtkMath::Min/Max? I was just inspired by "Common/Core/vtkDataArrayPrivate.txx". Thus no reason to not use vtkMath::Min/Max Replacement by vtkMath::Min/Max done !"
- [!5527](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5527) lorensen, 2019-06-21: "Why are these #define's needed? use std::min and std::max directly."
- [!5367](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5367) cory.quammen, 2019-04-03: "Do we support MSVC 2013? If so, it is safer to use `vtkMath::Min`/`Max` to avoid problem in MSVC 2013 (see !4255)."

### R073: Use emplace_back instead of push_back for vector insertion, and emplace instead of insert for associative containers.

Rationale: emplace_back can require less overhead to accomplish the same task as push_back, and emplace_back should remove the need for explicit make_pair; use emplace_back when the object supports move constructor to avoid a copy.

- Scope: C++ sources
- Support: 6 MRs, 9 threads, 2019-04-17 to 2023-02-27
- Reviewers: charles.gueunet (6), michael.migliore (1), seanm (1), timothee.chabat (1)
- [!9363](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9363) timothee.chabat, 2022-07-11: "use `emplace_back` instead of `push_back`"
- [!9230](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9230) charles.gueunet, 2022-06-15: "emplace_back should remove the need for the explicit make_pair"
- [!6779](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6779) seanm, 2020-04-21: "emplace_back and push_back have the same effect on sample_values, but emplace_back can require less overhead to accomplish the same task."

### R077: Initialize all member variables in the header file.

- Scope: C++ header files (for class member variables)
- Support: 6 MRs, 6 threads, 2020-05-24 to 2026-09-29
- Reviewers: mwestphal (4), charles.gueunet (1), cory.quammen (1)
- [!13687](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13687) mwestphal, 2026-09-29: "please move all init in header"
- [!12975](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12975) cory.quammen, 2026-03-17: "Do the initilizations in the header."
- [!11120](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11120) mwestphal, 2024-05-14: "you could initialize that in the header"

### R082: Use `const auto&` for loop variables when iterating over collections to avoid unnecessary copies.

*Mixed evidence: check the examples before accepting.*

Rationale: to avoid unnecessary copies

- Scope: C++ loop constructs iterating over collections (including maps)
- Support: 5 MRs, 8 threads, 2018-12-19 to 2025-12-13
- Reviewers: timothee.chabat (5), robertmaynard (1), sankhesh (1), jaswant.panchumarti (1)
- [!9231](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9231) timothee.chabat, 2022-06-07: "here and above, `const auto&` if tou don't change the value (and if possible)"
- [!5002](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5002) robertmaynard, 2018-12-19: "I would say this would be a perfect place for `auto`. ```cpp auto ldEnd = this->LocalData.end(); for (auto ldItr=this->LocalData.begin(); ldItr != ldEnd; ++ldItr ) { ... } ```"
- [!12237](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12237) jaswant.panchumarti, 2025-12-13: suggested `for (const auto& id : ids)`
- Counter-evidence:
  - [!9243](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9243) yohann.bearzi, 2022-06-06: suggested `for (auto& e : neighEdges) To avoid the overhead of calling the copy constructor for each edge.`

### R083: Do not guard `delete` or `delete[]` with a `nullptr` check.

*Mixed evidence: check the examples before accepting.*

Rationale: Because `delete` and `delete[]` are safe to call on null pointers (i.e., `delete nullptr` and `delete[] nullptr` are always valid and have no effect).

- Scope: C++ code using `delete` or `delete[]`
- Support: 5 MRs, 5 threads, 2017-07-10 to 2021-08-24
- Reviewers: dgobbi (1), mwestphal (1), jpouderoux (1), demarle (1), ben.boeckel (1)
- [!8332](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8332) ben.boeckel, 2021-08-24: "There's no need to guard `delete` with a `nullptr` check."
- [!6508](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6508) demarle, 2020-04-10: "To the best of my knowledge, checking for null before delete is unnecessary and redundant. https://github.com/ospray/ospray/blob/master/ospray/api/API.cpp#L541 Same goes with c++ delete, delete(nullpt"
- [!5424](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5424) jpouderoux, 2019-04-29: "if you use delete, you don't need to check value for nullity anymore #savelinesofcode"
- Counter-evidence:
  - [!12095](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12095) jaswant.panchumarti, 2025-05-01: "null check needed since `PickList` now has a setter. can you check the same in other places as well? ```suggestion:-0+0 if (this->PickList != nullptr) { this->PickList->Delete(); } ```"

### R084: Avoid using else blocks when the preceding if block ends with a return or otherwise completes the necessary logic.

*Mixed evidence: check the examples before accepting.*

- Scope: C++ sources
- Support: 5 MRs, 5 threads, 2018-02-12 to 2023-07-26
- Reviewers: mwestphal (2), utkarsh.ayachit (1), julien.fausty (1), lucas.givord (1)
- [!10353](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10353) lucas.givord, 2023-07-26: "you don't need to do it in a else section here"
- [!9792](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9792) julien.fausty, 2023-01-04: "could we do a `else if(this->SearchMethod == vtkPiecewiseFunction::InterpolationSearch)` and then have the `else` block be some error handling? Also, you can return directly from inside the conditiona"
- [!7607](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7607) utkarsh.ayachit, 2021-02-10: "I'd rewrite this...insert line 1162 at 1151 instead and then leave the else unchanged."
- Counter-evidence:
  - [!12305](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12305) louis.gombert, 2025-07-23: "instead of `if: return if: return ... raise()` you can do `if: ... elif: ... else: raise()`"

### R087: Indentation must be consistent and follow the specified style (e.g., two spaces shorter where required, no extra indentation).

- Scope: unspecified
- Support: 5 MRs, 5 threads, 2015-12-15 to 2024-08-21
- Reviewers: sankhesh (1), alouis (1), dgobbi (1), mzeyen (1), ben.boeckel (1)
- [!11003](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11003) ben.boeckel, 2024-08-21: "Indentation mismatch (here and elsewhere)"
- [!5335](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5335) mzeyen, 2019-04-17: "Indentation inconsistent with other documentation."
- [!3490](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3490) dgobbi, 2017-10-25: "There's a change in the indentation here. Indentation should be kept consistent."

### R093: Headers should be sorted alphabetically, optionally separated into sections with comments and newlines.

- Scope: C++ source files (implied by 'headers' in context of VTK C++ code reviews)
- Support: 5 MRs, 9 threads, 2018-01-25 to 2023-06-02
- Reviewers: michael.migliore (8), ben.boeckel (1)
- [!10253](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10253) ben.boeckel, 2023-06-02: "Same here: should be sorted. Or have a newline to separate into sections (maybe with a comment)."
- [!6812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6812) michael.migliore, 2020-04-30: "avoid empty lines between headers, and sort them"
- [!3816](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3816) michael.migliore, 2018-01-25: "headers are not ordered"

### R095: Use constexpr for compile-time constants, including member initializations in constructors and hard-coded values, and prefer constexpr over static for performance-critical functions to avoid implicit mutex checks; use const instead of constexpr when constexpr is not supported by the compiler.

Rationale: constexpr avoids implicit mutex checks in performance-critical functions and is appropriate for compile-time constants, while const is used when constexpr is not supported.

- Scope: C++ sources
- Support: 5 MRs, 5 threads, 2018-03-23 to 2026-01-14
- Reviewers: ken-martin (1), thomas.caissard (1), thomas.galland (1), mwestphal (1), ben.boeckel (1)
- [!12808](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12808) ben.boeckel, 2026-01-14: "Same as in the other `Alloc*` function and elsewhere in this function."
- [!9654](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9654) thomas.galland, 2022-11-10: "I think you can use `constexpr double ...` here has the value is hard-coded"
- [!7700](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7700) thomas.caissard, 2021-03-05: "Better not declare it `static` as it implicitly adds a mutex check each time you enter the function (and thus locks the cache line). `constexpr` would be better for that case!"

### R099: Do not use the `static` keyword for declarations inside an anonymous namespace.

Rationale: An anonymous namespace already provides internal linkage, making `static` redundant.

- Scope: C++ sources
- Support: 5 MRs, 5 threads, 2021-03-12 to 2026-06-30
- Reviewers: ben.boeckel (2), cory.quammen (1), yohann.bearzi (1), jaswant.panchumarti (1)
- [!13393](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13393) jaswant.panchumarti, 2026-06-30: "I believe the convention for statics is to declare within an anonymous namespace, but I might be wrong.. ```suggestion:-0+0 namespace { bool vtkOpenGLRenderWindowUseGenericBackend = false; } ```"
- [!9224](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9224) yohann.bearzi, 2022-06-14: "You should put this code in an anonymous namespace (and remove `static`, which is redundant inside such namespaces)"
- [!7835](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7835) cory.quammen, 2021-04-12: "I suspect clang-tidy will complain about redundancy of `static` in an anonymous namespace. They are both ways to declare something as having internal linkage, so only one or the other is needed (I wou"

### R107: Include standard library headers directly in header files where their types or functions are used, rather than relying on transitive inclusion.

Rationale: Because headers should not rely on other headers providing standard library includes, and missing includes can cause compilation errors on certain compilers/versions.

- Scope: C++ header files
- Support: 4 MRs, 4 threads, 2015-10-27 to 2024-03-15
- Reviewers: cory.quammen (1), ken-martin (1), lucas.givord (1), ben.boeckel (1)
- [!10969](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10969) ben.boeckel, 2024-03-15: "Why is this removed? We try not to rely on the header providing things like this."
- [!10302](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10302) lucas.givord, 2023-07-18: "please add `#include <array>` here instead of in the cxx"
- [!8510](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8510) ken-martin, 2021-11-02: "I believe std::isdigit requires cctype which is not included. Adding the include for cctype fixes the compile error."

### R108: Use the ternary operator for simple conditional assignments.

*Mixed evidence: check the examples before accepting.*

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2020-05-29 to 2025-09-26
- Reviewers: jpouderoux (1), charles.gueunet (1), julien.fausty (1), timothee.couble (1)
- [!10233](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10233) julien.fausty, 2023-08-07: "if (!this->CellInterfaceType) { // case intermediate interface with A and B processLeafCellWithDoubleInterface(cursor, scalarsInterfaceA, scalarsInterfaceB); } // case type == 1 just "right" interface"
- [!9567](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9567) charles.gueunet, 2022-09-23: "topology = polyOutput ? polyOutput->GetPolys() : ugOutput->GetCells();"
- [!12459](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12459) timothee.couble, 2025-09-26: suggested `if (auto cx = md.findChild("offset_x"); cx.valid()) { ox = cx.value<double>(); }`
- Counter-evidence:
  - [!11424](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11424) lucas.givord, 2024-08-26: "I believe nested ternary operation is bad for readability, could you please split that?"

### R113: Switch statements must include an explicit `default` case that produces an error for unexpected values.

Rationale: To handle unexpected values and avoid warnings on older compilers.

- Scope: C++ switch statements (inferred from context of VTK code reviews)
- Support: 4 MRs, 4 threads, 2015-03-27 to 2023-08-07
- Reviewers: dgobbi (1), mwestphal (1), charles.gueunet (1), julien.fausty (1)
- [!10233](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10233) julien.fausty, 2023-08-07: "`default` to error I would say just in case."
- [!10026](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10026) charles.gueunet, 2023-05-03: "Its ok, having an explicit default is still a good habit, and avoid some warning on older compiler, but ok for me."
- [!59](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/59) dgobbi, 2015-03-27: "If the behavior is to stay the same, I'd suggest adding an else rather than allowing fall-through:"

### R114: Do not declare a local variable with the same name as a class or a previously declared local variable in an outer scope.

Rationale: Shadowing triggers warnings in nightly testing.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2015-09-04 to 2023-11-22
- Reviewers: cory.quammen (1), dgobbi (1), utkarsh.ayachit (1), lucas.givord (1)
- [!10717](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10717) lucas.givord, 2023-11-22: "we should rename this variable `unstructuredGrid` or something like that :slight_smile:"
- [!7607](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7607) utkarsh.ayachit, 2021-02-17: "warning C4456: declaration of 'mpf' hides previous local declaration"
- [!2309](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2309) dgobbi, 2017-01-10: "Shadowing is forbidden because it triggers warnings in our nightly testing."

### R115: Declare loop variables in the loop initialization scope.

- Scope: C++ sources
- Support: 4 MRs, 5 threads, 2016-02-25 to 2026-07-02
- Reviewers: mhanwell (2), cory.quammen (1), louis.gombert (1), finetjul (1)
- [!13359](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13359) finetjul, 2026-07-02: "declare `t` in the for loop. Same for newValue and `interpolatedValue` (still used ?)"
- [!13288](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13288) louis.gombert, 2026-05-29: "It's usually better to declare the loop variable in the loop init like `for (size_t i=0...` instead of reusing it"
- [!1272](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1272) cory.quammen, 2016-03-08: "If you don't need `cellId` outside this scope, it is better to declare `cellId`s type here. That's a general principal - keep local variable declarations in the narrowest scope where they are needed."

### R118: Move variable declarations to the innermost block where they are used.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2016-12-06 to 2021-11-12
- Reviewers: jpouderoux (2), michael.migliore (1), dgobbi (1)
- [!8635](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8635) dgobbi, 2021-11-12: "move the `cfinfo` declaration to the inside of the block where `cfinfo` is used"
- [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) michael.migliore, 2020-03-06: "move variable declaration to line where it is used"
- [!4927](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4927) jpouderoux, 2018-11-28: "move variables where they are used"

### R120: Order directories and files alphabetically.

Rationale: for readability

- Scope: directories and files
- Support: 4 MRs, 4 threads, 2017-09-11 to 2024-06-24
- Reviewers: acbauer (1), tiffany.chhim (1), ben.boeckel (1), nicolas.vuaille (1)
- [!11254](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11254) nicolas.vuaille, 2024-06-24: "maybe order alphabetically for readability"
- [!10879](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10879) ben.boeckel, 2024-02-26: "Now all directories should be ordered."
- [!9232](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9232) tiffany.chhim, 2022-06-01: "Try to keep alphabetical order."

### R123: Remove deprecated, dead, or unused code that is no longer needed.

- Scope: unspecified
- Support: 4 MRs, 4 threads, 2018-04-18 to 2024-12-09
- Reviewers: mwestphal (2), dgobbi (1), lucas.givord (1)
- [!11695](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11695) lucas.givord, 2024-12-09: "Looks like we don't anymore"
- [!8675](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8675) mwestphal, 2021-12-27: "Please remove all dead code."
- [!4201](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4201) dgobbi, 2018-04-18: "The change looks good except for the `if False:`. Please just remove the old code, there's really no reason to keep it considering the checks that you have in place."

### R124: Place opening and closing braces on their own lines.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2018-11-21 to 2019-11-18
- Reviewers: jpouderoux (2), ken-martin (1), utkarsh.ayachit (1)
- [!6209](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6209) utkarsh.ayachit, 2019-11-18: "incorrect `{`...must be on a new line."
- [!5439](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5439) jpouderoux, 2019-04-18: "bad style ('{' should be on its line)"
- [!5380](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5380) ken-martin, 2019-04-09: "Style, braces on a separate line"

### R126: Class names should be in alphabetical order.

- Scope: unspecified
- Support: 4 MRs, 4 threads, 2019-10-14 to 2024-02-07
- Reviewers: yohann.bearzi (2), ben.boeckel (1), nicolas.vuaille (1)
- [!6609](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6609) yohann.bearzi, 2020-03-23: "Those class name need to be sorted in alphabetical order."
- [!6066](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6066) yohann.bearzi, 2019-10-14: "`class` names should be in alphabetical order."
- [!10869](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10869) nicolas.vuaille, 2024-02-07: "alphabetical order"

### R127: Use clang-format off/on blocks to suppress formatting for specific blocks or lines where manual formatting must be preserved.

Rationale: To prevent clang-format from breaking code that requires specific spacing or includes, or to preserve original manual formatting.

- Scope: C++ source files (implied by use of clang-format and specific C++ code examples in evidence)
- Support: 4 MRs, 4 threads, 2019-12-02 to 2024-03-04
- Reviewers: ben.boeckel (1), utkarsh.ayachit (1), mwestphal (1), jaswant.panchumarti (1)
- [!10898](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10898) jaswant.panchumarti, 2024-03-04: "missing clang-format off...clang-format on"
- [!9505](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9505) mwestphal, 2022-08-30: "maybe disable clang format on this file ? ... done, with the original formatting kept"
- [!7507](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7507) utkarsh.ayachit, 2021-01-06: "add `/* clang-format off */` ... `/* clang-format on */` around these to avoid clang format from messing with the spacing ...this won't compile otherwise."

### R129: Use `this->Superclass::MethodName` syntax when calling superclass methods.

- Scope: C++ sources
- Support: 4 MRs, 5 threads, 2020-07-13 to 2025-03-17
- Reviewers: utkarsh.ayachit (4), mwestphal (1)
- [!7844](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7844) utkarsh.ayachit, 2021-04-13: "If you're simply calling superclass, use `this->Superclass::GetCellNeighbors`; that keeps the intent clear."
- [!7101](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7101) utkarsh.ayachit, 2020-07-13: "all calls to `Superclass::...` must be written as `this->Superclass::...`"
- [!11957](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11957) mwestphal, 2025-03-17: suggested `this->Superclass::SetNumberOfInputPorts(1);`

### R130: Declare variables that are compile-time constants as `static constexpr` and name them in ALL_CAPS.

- Scope: C++ code
- Support: 4 MRs, 4 threads, 2021-01-22 to 2025-04-08
- Reviewers: mwestphal (2), ben.boeckel (1), nicolas.vuaille (1)
- [!12021](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12021) mwestphal, 2025-04-08: "all these should be constexpr (or const at least)"
- [!8406](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8406) nicolas.vuaille, 2021-09-14: "I think we prefer uppercase for constexpr variable names"
- [!8182](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8182) ben.boeckel, 2021-08-05: "These should all be declared `static` or `constexpr`, no?"

### R131: Add new enum values at the end of an existing enum, explicitly set their integer values, and avoid inserting new values in the middle to preserve index correspondence and API compatibility.

Rationale: To avoid breaking index correspondence and APIs that rely on the enum's declaration order implicitly, and to prevent future errors in testing.

- Scope: C++ enum definitions
- Support: 4 MRs, 4 threads, 2021-09-08 to 2024-06-03
- Reviewers: julien.fausty (2), finetjul (1), lucas.givord (1)
- [!11165](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11165) lucas.givord, 2024-06-03: "we should generally set the first value of an enum (to avoid error in the future for some testing...)"
- [!10197](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10197) julien.fausty, 2023-05-15: "Here and everywhere this ordering would impact: I would argue to not insert `PROCESSIDS` in the middle since this is going to move all the index correspondence and change all the APIs that rely on thi"
- [!9599](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9599) julien.fausty, 2022-10-06: "The presence of this clamp macro is all the more important I think to explicitly set the integer value of your enum. I know that the standard now is to increment enums in the order of their declaratio"

### R132: Use const reference for function parameters that are not modified.

Rationale: To avoid copying and because the parameter is not modified by the function.

- Scope: C++ function parameters
- Support: 4 MRs, 5 threads, 2021-10-05 to 2024-06-25
- Reviewers: thomas.galland (3), ben.boeckel (1), jaswant.panchumarti (1)
- [!11261](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11261) jaswant.panchumarti, 2024-06-25: "Can this be `const`? No one else modifies the map. It's only passed in the call to `CalculateAngles` which happens to use `const`. ```suggestion:-0+0 const vtkPolyhedron::vtkPointIdMap& pointIdMap) ``"
- [!10322](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10322) thomas.galland, 2023-07-07: "`const std::set<std::string>&` ?"
- [!8650](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8650) thomas.galland, 2021-12-09: "const std::list<int>& valueList"

### R133: Initialize std::vector with size and default value in the constructor instead of default-constructing then resizing or assigning in a loop or after resize.

- Scope: C++ sources
- Support: 4 MRs, 6 threads, 2022-05-12 to 2025-07-24
- Reviewers: mwestphal (3), spiros.tsalikis (1), charles.gueunet (1), leon.victor (1)
- [!11285](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11285) leon.victor, 2024-08-26: "Use https://en.cppreference.com/w/cpp/container/vector/vector (3) ? (here an below)"
- [!10609](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10609) charles.gueunet, 2023-10-24: "std::vector<vtkIdType> outPointIds = { ptId1, ptId2 }; to avoid unneeded reallocation."
- [!9148](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9148) spiros.tsalikis, 2022-05-12: "No need to use fill, do the following. ```c++ std::vector<vtkIdType> pointIdRedirectionMap(numPoints, -1); ```"

### R135: Use the do-while(0) idiom in function-like macros to ensure correct semicolon usage and prevent issues when macros are used in conditional statements without braces.

Rationale: Without it, the semicolon at the usage site becomes extraneous or causes syntax errors, and the macro may fail when used in conditions without braces.

- Scope: function-like macros in C++
- Support: 4 MRs, 4 threads, 2022-06-28 to 2026-04-21
- Reviewers: mwestphal (2), ben.boeckel (1), lucas.givord (1)
- [!13159](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13159) mwestphal, 2026-04-21: "the do-while(0) idiom is used to force the user of a function-like macro to end the statement with a semi-colon. otherwise, after preprocessing, the semi-colon appears extraneous (which is the warning"
- [!10330](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10330) lucas.givord, 2023-07-21: "as it's to avoid bad semicolon behavior with c macro, you can do your `do while(false)` at the end of the macro right? This also handle potential problems with conditions: https://gcc.gnu.org/onlinedo"
- [!10081](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10081) ben.boeckel, 2023-03-27: "Please use the `do { } while (0)` trick as this fails when used in a condition without braces: ``` if (some_cond) Check(expr, msg); ```"

### R136: Insert a separator line `//------------------------------------------------------------------------------` above certain code blocks, and use `//----------` only for comment separators.

- Scope: unspecified
- Support: 4 MRs, 4 threads, 2023-03-10 to 2024-11-07
- Reviewers: lucas.givord (2), mwestphal (2)
- [!11602](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11602) mwestphal, 2024-11-07: "//------------------------------------------------------------------------------ add `//------------------------------------------------------------------------------` above"
- [!10638](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10638) lucas.givord, 2023-11-09: "here and below, add missing `//------------------------------------------------------------------------------`"
- [!10659](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10659) mwestphal, 2023-11-07: "//------------------------------------------------------------------------------ // add `//------------------------------------------------------------------------------` everywhere needed"

### R142: Declare variables at the point of first use within a method, not at the top of the function.

- Scope: C++ source code
- Support: 3 MRs, 3 threads, 2017-03-13 to 2026-08-24
- Reviewers: mwestphal (2), lucas.givord (1)
- [!13621](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13621) mwestphal, 2026-08-24: "please declare that in each method, no need to put this here."
- [!11233](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11233) lucas.givord, 2024-06-18: "you can declare `numDim` just before to use it"
- [!2582](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2582) mwestphal, 2017-03-13: "you can declare i here"

### R143: Capitalize the first letter of every attribute name.

*Mixed evidence: check the examples before accepting.*

- Scope: attributes
- Support: 3 MRs, 3 threads, 2018-01-17 to 2020-09-21
- Reviewers: yohann.bearzi (2), mwestphal (1)
- [!7247](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7247) yohann.bearzi, 2020-09-21: "Please add a cap on first letter of every attributes. For instance, replace `pointToIncidentFaces` by `PointToIncidentFaces`."
- [!6295](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6295) yohann.bearzi, 2019-12-12: "Naming convention: first letter should be upper case. Same thing for `addPoints`."
- [!3745](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3745) mwestphal, 2018-01-17: "first leter caps"
- Counter-evidence:
  - [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) michael.migliore, 2020-03-10: "use lower case for the first letter here. You can rename the variable to `reader`"

### R148: Prefer `using` over `typedef`

*Mixed evidence: check the examples before accepting.*

Rationale: for consistency (and `using` is universally applicable where `typedef` cannot be used, such as in iterator frameworks)

- Scope: C++ sources
- Support: 3 MRs, 4 threads, 2021-02-22 to 2022-05-31
- Reviewers: alliepiper16 (2), charles.gueunet (2)
- [!9230](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9230) charles.gueunet, 2022-05-31: "prefer `using` over `typedef`"
- [!8052](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8052) charles.gueunet, 2021-07-01: "prefer `using` over `typedef`"
- [!7647](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7647) alliepiper16, 2021-02-22: "Please use the newer `using` syntax instead of `typedef` for consistency."
- Counter-evidence:
  - [!8755](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8755) will.schroeder, 2021-12-20: "I think it is more coherent with the whole file to keep the typedef."

### R149: Initialize member pointers to nullptr in the header (or constructor) before calling setter methods that may use them, and prefer header initialization for integers and pointers in new VTK classes.

*Mixed evidence: check the examples before accepting.*

- Scope: C++ class member initialization in new VTK classes
- Support: 3 MRs, 3 threads, 2021-06-16 to 2024-12-03
- Reviewers: timothee.chabat (1), utkarsh.ayachit (1), jaswant.panchumarti (1)
- [!11567](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11567) jaswant.panchumarti, 2024-12-03: "Please set defaults for integers, and initlaize pointers to `nullptr` in the header rather than doing it in constructor. IIRC, This is how new VTK classes should be written."
- [!8391](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8391) utkarsh.ayachit, 2021-09-08: "this is not correct. `OutputGhostArrayName` needs be initialized to nullptr before calling `SetOutputGhostArrayName`. ```c++ vtkExtractGhostCells::vtkExtractGhostCells() : OutputGhostArrayName(nullptr"
- [!7721](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7721) timothee.chabat, 2021-06-16: "nullptr initialization is done by vtkSmartPointer by default"
- Counter-evidence:
  - [!9616](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9616) dgobbi, 2022-10-12: "Since `this->LookupTable` is a `vtkSmartPointer`, there is no need to set it to `nullptr` in the `vtPlotBar` constructor."

### R154: Keep lines under 80 characters.

- Scope: unspecified
- Support: 3 MRs, 3 threads, 2015-09-09 to 2017-06-16
- Reviewers: alliepiper16 (2), demarle (1)
- [!2930](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2930) demarle, 2017-06-16: "split long lines <=80 chars please"
- [!1657](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1657) alliepiper16, 2016-07-13: "Line length should be <80 characters"
- [!397](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/397) alliepiper16, 2015-09-09: "Please keep lines under 80 characters. This can be split like: ..."

### R158: Use `unsigned int` or `uint32_t` for loop counters instead of `unsigned` or `int`.

Rationale: to avoid signed/unsigned comparison warnings

- Scope: loop variable declarations
- Support: 3 MRs, 3 threads, 2016-05-18 to 2023-02-03
- Reviewers: dgobbi (1), mwestphal (1), timothee.chabat (1)
- [!1502](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1502) dgobbi, 2016-05-18: "for (int i` -> `for (unsigned int i"
- [!9912](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9912) timothee.chabat, 2023-02-03: "vector<unsigned int>"
- [!5377](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5377) mwestphal, 2019-04-16: "`uint32_t`"

### R159: Use VecTraits::GetComponent to safely access vector components instead of assuming operator[] exists, and prefer operator[] over at() for vector access when bounds checking is unnecessary.

Rationale: Some vector types (e.g., vtkm::Range) have VecTraits reporting component counts but no operator[], and std::vector::at() performs unnecessary bounds checking when operator[] suffices.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2016-08-19 to 2023-03-15
- Reviewers: msmolens (1), timothee.chabat (1), kmorel (1)
- [!9925](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9925) kmorel, 2023-03-15: "Here you are assuming that `VecType` has an `operator[]` that is consistent with a `Vec`. That might not be the case. For example, `vtkm::Range` has a `VecTraits` that will report it as having 2 compo"
- [!9170](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9170) timothee.chabat, 2022-05-10: "Also please stay consistent with `operator[]` and `at()` usage (imo prefer `[]`)"
- [!1845](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1845) msmolens, 2016-08-19: "std::vector::at() performs bounds checking. operator[] is more appropriate here."

### R161: Replace magic numbers with named constants using `constexpr` in an anonymous namespace or symbolic names such as `vtkDataSetAttributes::DUPLICATECELL`.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2017-01-16 to 2023-07-21
- Reviewers: danlipsa (1), utkarsh.ayachit (1), thomas.galland (1)
- [!10330](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10330) thomas.galland, 2023-07-21: "please comment these "magic" numbers (or name them with `constexpr` in an anonymous namespace)"
- [!8391](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8391) utkarsh.ayachit, 2021-09-08: "I'd use `vtkDataSetAttributes::DUPLICATECELL` instead of 1 to make it obvious where this 1 comes from."
- [!2348](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2348) danlipsa, 2017-01-16: "I would use the symbolic name"

### R162: Put a space after the 'for' keyword.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2017-02-17 to 2019-04-23
- Reviewers: mwestphal (1), jpouderoux (1), michael.migliore (1)
- [!4707](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4707) jpouderoux, 2018-09-26: "formatting: please put space after keywords (for, if, while etc)"
- [!5038](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5038) michael.migliore, 2019-04-23: "space after `for`"
- [!2486](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2486) mwestphal, 2017-02-17: "spacing "for (""

### R163: Add spaces for proper spacing.

- Scope: unspecified
- Support: 3 MRs, 3 threads, 2017-02-17 to 2018-01-16
- Reviewers: mwestphal (2), jpouderoux (1)
- [!3767](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3767) mwestphal, 2018-01-16: "spacing, here and everywhere."
- [!3604](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3604) jpouderoux, 2017-12-12: "add spaces"
- [!2486](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2486) mwestphal, 2017-02-17: "spacing"

### R164: Use 'the source' instead of 'it', 'its' instead of 'is', and 'it' instead of 'in' in comments.

- Scope: comments
- Support: 3 MRs, 3 threads, 2017-03-21 to 2023-08-11
- Reviewers: alouis (1), luzpaz (1), tiffany.chhim (1)
- [!10399](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10399) tiffany.chhim, 2023-08-11: ""it" -> "the source""
- [!4086](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4086) luzpaz, 2018-03-20: "The `is` should be `its`: // Whether its representation can handle a selection."
- [!2513](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2513) alouis, 2017-03-21: "in in -> it in"

### R166: Place opening braces on the same line as the control statement (e.g., if, else, for, range-based for).

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2017-05-05 to 2025-09-05
- Reviewers: ken-martin (1), dgobbi (1), mwestphal (1)
- [!2772](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2772) ken-martin, 2017-05-05: "You may not be aware but we changed the coding style for VTK a couple months ago. The new standard requires braces to be in line with the if/else statement"
- [!12430](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12430) mwestphal, 2025-09-05: suggested `for (const auto& [id, coords] : expectedValues) {`
- [!11506](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11506) dgobbi, 2024-09-23: "Braces, `this`."

### R171: Place supporting classes and methods for a test in an anonymous namespace in the test file.

Rationale: A named namespace in a test is unnecessary and risks name collisions.

- Scope: tests
- Support: 3 MRs, 3 threads, 2017-10-30 to 2026-07-06
- Reviewers: alliepiper16 (1), lucas.givord (1), mwestphal (1)
- [!10995](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10995) lucas.givord, 2024-04-11: "even for testing I believe adding all of these methods in an anonymous namespace is a good practice, wdyt?"
- [!3513](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3513) alliepiper16, 2017-10-30: "Generally, it's best to put all supporting classes, etc for a test in an anonymous namespace in the test file"
- [!13361](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13361) mwestphal, 2026-07-06: suggested `namespace I dont see the point of a named namespace in a test, and there is a chance of name collision.`

### R173: Do not perform unnecessary casts or downcasts; use only correct casts when needed.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2018-01-11 to 2026-06-03
- Reviewers: mwestphal (1), timothee.chabat (1), nicolas.vuaille (1)
- [!13256](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13256) nicolas.vuaille, 2026-06-03: "no need to downcast"
- [!9363](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9363) timothee.chabat, 2022-07-08: "int / float := float no need for cast here"
- [!3767](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3767) mwestphal, 2018-01-11: "use correct cast"

### R174: Use clang-format to format code.

Rationale: It is part of the contribution workflow dedicated to running conformity checks.

- Scope: unspecified
- Support: 3 MRs, 3 threads, 2018-01-11 to 2023-04-19
- Reviewers: mwestphal (1), sebastien.jourdain (1), halowine (1)
- [!10109](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10109) halowine, 2023-04-19: "It is part of the contribution workflow dedicated to running conformity checks. In this instance it looks like it failed due to the formatting of the changes which were not conform to the `clang-forma"
- [!5271](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5271) sebastien.jourdain, 2019-03-05: "You may want to use clang-format with the ParaView config file."
- [!3767](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3767) mwestphal, 2018-01-11: "spacing in all this file. I would recommend using clang-format -i"

### R180: Sort items in alphabetical order

- Scope: unspecified
- Support: 3 MRs, 3 threads, 2018-11-26 to 2024-01-23
- Reviewers: michael.migliore (1), louis.gombert (1), charles.gueunet (1)
- [!10833](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10833) charles.gueunet, 2024-01-23: "alphabetic order"
- [!10732](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10732) louis.gombert, 2023-11-30: "Sort alphabetically"
- [!4909](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4909) michael.migliore, 2018-11-26: "alphabetical order"

### R183: Use curly braces.

- Scope: unspecified
- Support: 3 MRs, 3 threads, 2019-04-09 to 2023-03-15
- Reviewers: ken-martin (1), cory.quammen (1), LucasGandelKitware (1)
- [!10026](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10026) LucasGandelKitware, 2023-03-15: "use braces"
- [!7806](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7806) cory.quammen, 2021-04-02: "Need curly braces."
- [!5380](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5380) ken-martin, 2019-04-09: "Style braces"

### R187: Each header include must have a comment explaining why it is needed.

- Scope: header files
- Support: 3 MRs, 3 threads, 2019-11-25 to 2025-12-30
- Reviewers: demarle (1), mwestphal (1), sankhesh (1)
- [!12747](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12747) sankhesh, 2025-12-30: "Without that comment, the HeaderTest is failing on this MR."
- [!11602](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11602) mwestphal, 2024-11-14: "each header include should have a comment explaining why its needed eg: #include "vtkSmartPointer.h" // for smart pointer"
- [!6231](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6231) demarle, 2019-11-25: "One of the regression tests checks vtk code guidelines such as does a public header file have only one include in it. Two workarounds for that are to 1) add a comment to justify the extra includes, 2)"

### R190: Use descriptive variable names that reflect the variable's purpose, content, or direction of iteration.

- Scope: unspecified
- Support: 3 MRs, 3 threads, 2020-03-06 to 2023-12-22
- Reviewers: michael.migliore (1), timothee.chabat (1), jcfr (1)
- [!10783](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10783) jcfr, 2023-12-22: "Why is the ivar called `oldcam` ? Should it be `activecam` instead ?"
- [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) michael.migliore, 2020-03-06: "I renamed nbLines into nbLinesLeft"
- [!9170](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9170) timothee.chabat, 2022-05-10: "i -> axis"

### R191: Prefix standard library types with `std::` (e.g., `std::size_t`, `std::istream`)

- Scope: C++ code
- Support: 3 MRs, 3 threads, 2020-03-10 to 2025-12-09
- Reviewers: michael.migliore (1), charles.gueunet (1), lucas.givord (1)
- [!12699](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12699) lucas.givord, 2025-12-09: "maybe it's time for some clean in this code, every `size_t` should be prefixed by his namespace so `std::size_t`"
- [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) michael.migliore, 2020-03-10: "add `std::` before all `istream` occurrences"
- [!9471](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9471) charles.gueunet, 2022-08-18: "same, `std::`"

### R192: Methods intended only for internal use should be private unless they are intended to be used by inheriting classes.

Rationale: Because they are internal implementation details and not meant for external or inheritance use, and for deprecation purposes.

- Scope: C++ class method declarations (specifically in VTK classes)
- Support: 3 MRs, 3 threads, 2020-03-10 to 2026-08-24
- Reviewers: jpouderoux (1), thomas.galland (1), mwestphal (1)
- [!13551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13551) mwestphal, 2026-08-24: "Unless it is intended to be used by inheriting classes, but I doubt it."
- [!10587](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10587) thomas.galland, 2023-10-13: "I think you can move all the internal methods to `private`, since you're class is not (at least for now) intended to be inherited from, and for deprecation purposes"
- [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) jpouderoux, 2020-03-10: "I would put all the following methods as protected instead (this is usually done like this in VTK)"

### R196: Use 'you' instead of 'user' or 'The user' in documentation.

Rationale: The person reading the documentation is the 'you', so it is more direct and natural to address them as such.

- Scope: documentation
- Support: 3 MRs, 3 threads, 2020-08-10 to 2026-07-22
- Reviewers: nicolas.vuaille (2), cory.quammen (1)
- [!13486](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13486) nicolas.vuaille, 2026-07-22: "```diff - This allows user to write + This allows you to write ```"
- [!11424](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11424) nicolas.vuaille, 2024-08-26: "users can -> you can"
- [!7152](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7152) cory.quammen, 2020-08-10: ""The user" is the one reading this documentation, so you can just write "You"."

### R197: Declare variables one per line.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2021-01-08 to 2026-05-29
- Reviewers: finetjul (1), cory.quammen (1), lucas.givord (1)
- [!13288](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13288) lucas.givord, 2026-05-29: "these variables init/declaration don't follow vtk classic convention"
- [!9087](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9087) cory.quammen, 2022-04-26: "For modern VTK we really should be in the habit of defining variables as close to where they are used as possible."
- [!7504](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7504) finetjul, 2021-01-08: "vtk style requires 1 variable declaration per line."

### R199: Declare and define variables outside loops when their values do not change across iterations.

- Scope: unspecified
- Support: 3 MRs, 3 threads, 2021-03-03 to 2026-09-28
- Reviewers: mwestphal (1), spiros.tsalikis (1), corentin.munoz (1)
- [!13735](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13735) corentin.munoz, 2026-09-28: "You can define it once and only changing the time step in the loop"
- [!8895](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8895) spiros.tsalikis, 2022-04-11: "double converge = this->Convergence; int numIter = this->NumberOfIterations; double relax = this->RelaxationFactor; Since these variables don't change, there is no need to be set."
- [!7709](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7709) mwestphal, 2021-03-03: "declare outside of loop"

### R201: Factorize duplicated code blocks into a single function when working with data objects.

- Scope: C++ code dealing with data objects
- Support: 3 MRs, 3 threads, 2021-09-01 to 2023-12-07
- Reviewers: LucasGandelKitware (1), mwestphal (1), lucas.givord (1)
- [!10744](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10744) lucas.givord, 2023-12-07: "could be factorize with the previous one"
- [!10459](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10459) mwestphal, 2023-08-31: "you can work with a dataobject and factorize these two"
- [!8303](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8303) LucasGandelKitware, 2021-09-01: "Can you factorize this in one function and have this->TranslateAxis(...) the same way it is done for this->RotateAxis..."

### R202: Initialize variables at declaration or in the constructor.

Rationale: to avoid uninitialized values

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2021-11-05 to 2026-07-09
- Reviewers: francois.mazen (1), mwestphal (1), lucas.givord (1)
- [!13429](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13429) lucas.givord, 2026-07-09: "we could init these variable to 0 in each case, right ? So we can do that when we declare them"
- [!10026](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10026) mwestphal, 2023-03-08: "it would be better and more modern yes."
- [!8611](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8611) francois.mazen, 2021-11-05: "Please also initialize `ptId` to 0."

### R203: Use VTK_FALLTHROUGH macro for intentional fall-through cases in switch statements where the case contains actual code.

Rationale: It is the VTK equivalent of the C++11 [[fallthrough]] attribute, used as a clue to developers about intentional fallthrough.

- Scope: switch statements in C++ code
- Support: 3 MRs, 3 threads, 2022-01-12 to 2022-12-16
- Reviewers: mwestphal (2), scott.wittenburg (1)
- [!9757](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9757) scott.wittenburg, 2022-12-16: "this is the VTK equivalent, C++11 compatible of https://en.cppreference.com/w/cpp/language/attributes/fallthrough"
- [!9398](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9398) mwestphal, 2022-08-11: "you need VTK_FALLTHROUGH only when your case contains actual code."
- [!8804](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8804) mwestphal, 2022-01-12: "VTK_FALLTHROUGH"

### R205: Use brace initialization for arrays.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2022-05-31 to 2023-08-10
- Reviewers: julien.fausty (2), charles.gueunet (1)
- [!9812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9812) julien.fausty, 2023-05-05: "-0+0 double deriv[3] = { 0.0 }; double values[8] = { 0.0 };"
- [!9230](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9230) charles.gueunet, 2022-05-31: "using: ```suggestion:-0+0 std::array<unsigned int, 3> bin{}, ``` you won't need the `std::fill` below"
- [!10233](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10233) julien.fausty, 2023-08-10: suggested `double xyz[3] = { 0.0, 0.0, 0.0 };`

### R206: Avoid first-person pronouns (I, we) and second-person pronouns (you, your) in comments

- Scope: comments
- Support: 3 MRs, 3 threads, 2022-06-06 to 2024-03-11
- Reviewers: mwestphal (1), tiffany.chhim (1), louis.gombert (1)
- [!10951](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10951) louis.gombert, 2024-03-11: "Don't use first person or personal judgement"
- [!9468](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9468) tiffany.chhim, 2022-09-19: "I think we should avoid using words such as "you", or "your", so: `if the input`"
- [!9230](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9230) mwestphal, 2022-06-06: "Avoid I and We in comments"

### R210: Use std::clamp for clamping values, or std::max for single-bound clamping, or a double ternary operator (min(max(x, min), max)) when std::clamp is unavailable.

- Scope: C++ sources
- Support: 3 MRs, 4 threads, 2023-04-28 to 2025-12-10
- Reviewers: mwestphal (2), lucas.givord (1), spiros.tsalikis (1)
- [!12321](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12321) spiros.tsalikis, 2025-12-10: "would std::clamp be useful here? Yes. Done."
- [!10169](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10169) lucas.givord, 2023-04-28: "I have seen it around in other places. Here is is essentially a clamp macro. (And it is actually how the clamp macro is implemented: https://gitlab.kitware.com/vtk/vtk/-/blob/master/Common/Core/vtkSet"
- [!12611](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12611) mwestphal, 2025-11-18: "std::max ?"

### R211: All files must include an SPDX license identifier at the beginning, with the SPDX copyright as the first line.

- Scope: all files
- Support: 3 MRs, 4 threads, 2023-05-24 to 2026-09-16
- Reviewers: lucas.givord (2), julien.fausty (1), jcfr (1)
- [!13715](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13715) lucas.givord, 2026-09-16: "all files should have spdx at the beginning no?"
- [!13312](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13312) lucas.givord, 2026-07-02: "new files require SPDX mention"
- [!10200](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10200) jcfr, 2023-05-31: "Looks similar, in any case this is a required field of the .spdx file: https://spdx.github.io/spdx-spec/v2.2.2/package-information/#715-declared-license-field"

### R212: Declare new member variables in the private section of a class.

- Scope: C++ class definitions
- Support: 3 MRs, 3 threads, 2023-10-09 to 2026-02-05
- Reviewers: lucas.givord (1), mwestphal (1), olesen (1)
- [!12885](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12885) olesen, 2026-02-05: "also put it in the `private` section (modern VTK style)"
- [!10585](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10585) lucas.givord, 2023-10-09: "could you please move this variable in the `private` section below?"
- [!12582](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12582) mwestphal, 2025-11-05: "lets private it"

### R214: Use == for comparisons in conditional statements (including while loops and if statements) to avoid assignment bugs and ensure correct logic.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2024-02-05 to 2026-03-24
- Reviewers: mwestphal (2), nicolas.vuaille (1)
- [!12934](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12934) mwestphal, 2026-03-24: "while (pos = str.find(';') != std::string::npos)"
- [!10851](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10851) nicolas.vuaille, 2024-02-05: "-0+0 if (notation == vtkNumberToString::Notation::Fixed && (value > 9e59 || value < 9e-59))"
- [!12852](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12852) mwestphal, 2026-03-12: suggested `// The output must have only one arrays, "Colors" // Check the number of arrays if (data->GetPointData()->GetNumberOfArrays() == 1)`

## process-ci

### R001: Squash commits into logical commits (or a single commit) before merging.

Rationale: to make the history clearer

- Scope: unspecified
- Support: 38 MRs, 40 threads, 2015-03-31 to 2023-03-22
- Reviewers: mwestphal (17), jpouderoux (5), utkarsh.ayachit (4), dgobbi (3), michael.migliore (3)
- [!7521](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7521) mwestphal, 2023-03-22: "Great, please squash your two commits into one and force push."
- [!8648](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8648) mwestphal, 2022-02-03: "please squash your commits logcically"
- [!7219](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7219) mwestphal, 2022-02-02: "please squash your commits into one"

### R006: Rebase on master and run CI again.

Rationale: to ensure green CI and resolve build issues

- Scope: unspecified
- Support: 22 MRs, 22 threads, 2016-05-15 to 2026-06-19
- Reviewers: mwestphal (10), cory.quammen (6), LucasGandelKitware (1), williamfgc (1), rupertnash (1)
- [!13353](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13353) mwestphal, 2026-06-19: "Prefer rebasing on master for cleaner CI."
- [!12121](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12121) berkgeveci, 2025-05-16: "Rebase onto current release. Create MR targeting master."
- [!11319](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11319) mwestphal, 2024-08-08: "please rebase on master and force push"

### R028: Rebase the change onto the release branch and add `Backport: release` to the GitLab MR description.

Rationale: so that the bot will backport to the release branch when it's merged

- Scope: unspecified
- Support: 11 MRs, 13 threads, 2015-08-04 to 2026-08-31
- Reviewers: dgobbi (2), mwestphal (2), sankhesh (2), ben.boeckel (1), dcthomp (1)
- [!13646](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13646) mwestphal, 2026-08-31: "please rebase on release and add `Backport: release` at the end of the description"
- [!13415](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13415) sankhesh, 2026-07-05: "For the backport to work, the `Backport: release` trailer needs to be added to the MR description at the very top of the page, rather than in the comments."
- [!12121](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12121) sankhesh, 2025-05-19: "The `Backport: release` should be in the MR description."

### R035: When backporting changes to the paraview/release branch, rebase the branch on paraview/release and add 'Backport: paraview/release' to the end of the merge request description.

*Mixed evidence: check the examples before accepting.*

- Scope: unspecified
- Support: 9 MRs, 9 threads, 2020-05-11 to 2024-09-18
- Reviewers: cory.quammen (6), boonth (1), caitlin.ross (1), mwestphal (1)
- [!11485](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11485) mwestphal, 2024-09-18: "you need either a bypass token or rebase on lastet paraview/release"
- [!11460](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11460) cory.quammen, 2024-09-06: "API changes should definitely not go in `paraview/release`, let me check the list. Indeed, https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11317 is not a bug fix, should not be backported. https:/"
- [!10100](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10100) caitlin.ross, 2023-03-29: "Oh wait, need to merge into paraview/release, not master."
- Counter-evidence:
  - [!11237](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11237) mwestphal, 2024-06-17: "Lets not bacckport anything for now, please merge in master only or wait for ParaView release process to complete: https://discourse.vtk.org/t/please-do-not-backport-to-release-or-paraview-release-bra"

### R036: Use `git cherry-pick -x` when cherry-picking commits to record the original commit SHA in the commit message.

Rationale: To track the original commit and preserve commit history, especially when rebasing on new releases.

- Scope: unspecified
- Support: 9 MRs, 10 threads, 2016-02-03 to 2024-01-30
- Reviewers: cory.quammen (3), ben.boeckel (2), utkarsh.ayachit (2), lucas.givord (2), seanm (1)
- [!10846](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10846) lucas.givord, 2024-01-30: "could you please use `cherry-pick -x` ?"
- [!10847](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10847) lucas.givord, 2024-01-30: "could you please use `cherry-pick -x` (we can track the original commit with this option) ?"
- [!9609](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9609) cory.quammen, 2022-10-07: "I should have asked you to use the option `-x` (e.g., `git cherry-pick -x`) to record the original commit SHA that was backported."

### R040: Use `Do: test -s quick` before running full tests (`Do: test`) to catch early errors and conserve CI resources

Rationale: CI runners are busy and to avoid wasting CI cycles while not all jobs are likely to pass, and to reduce testing load on the CI

- Scope: merge request testing workflows in VTK CI
- Support: 9 MRs, 9 threads, 2024-06-07 to 2026-02-20
- Reviewers: mwestphal (5), cory.quammen (2), louis.gombert (2)
- [!12923](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12923) louis.gombert, 2026-02-20: "As a reminder, you can use `Do: test -s quick` to run minimal test suite and catch most CI errors, and avoid wasting CI cycles while you're not sure all jobs will pass"
- [!12918](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12918) louis.gombert, 2026-02-12: "Also CI runners are very busy this week, please use `Do: test -s quick` instead of full tests when possible to save cycles @mathurin.lemarie"
- [!12784](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12784) mwestphal, 2026-01-09: "please prefer `Do: test -s quick` until quick stage passes."

### R055: Rebase the topic branch on master instead of merging master into the branch to avoid merge commits.

*Mixed evidence: check the examples before accepting.*

- Scope: topic branches for merge requests
- Support: 7 MRs, 7 threads, 2018-01-02 to 2025-07-10
- Reviewers: dgobbi (2), alliepiper16 (1), fdepourcq (1), cory.quammen (1), akaszynski (1)
- [!12273](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12273) dgobbi, 2025-07-10: "we generally do not accept MRs that contain merge commits. Commits from master must be brought into the topic branch by rebasing the branch on master, rather than by merging master into the branch."
- [!11997](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11997) sankhesh, 2025-03-21: "you shouldn't be making a merge request against the release branch. Please fix your fork based on Cory's comments above Rebase these changes onto the release branch Change the target of the merge requ"
- [!8092](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8092) akaszynski, 2021-06-22: "FWIW, we prefer to rebase so that the topic is just your commits instead of also bringing in changes from `master`."
- Counter-evidence:
  - [!5337](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5337) ben.boeckel, 2019-03-28: "When we merge that will put it into both branches. I'll do it here, but the other MRs should do the same if they also should go into `master`."

### R056: CI must be run and green before merging.

- Scope: unspecified
- Support: 7 MRs, 7 threads, 2022-05-21 to 2026-09-01
- Reviewers: mwestphal (5), spiros.tsalikis (1), seanm (1)
- [!13636](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13636) mwestphal, 2026-09-01: "It lets you merge even when build CI is red. https://discourse.vtk.org/t/green-ci-now-required-to-merge-branches/9389"
- [!12734](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12734) mwestphal, 2025-12-19: "once if have a green CI, you can merge whenever you want once the backport is ready."
- [!10991](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10991) mwestphal, 2024-03-26: "Please avoid merging without checking the CI."

### R066: Split commits or merge requests into distinct, logically coherent units focused on a single issue.

Rationale: It facilitates the review process by making changes easier to understand, review, and address.

- Scope: unspecified
- Support: 6 MRs, 6 threads, 2017-09-18 to 2026-03-18
- Reviewers: cory.quammen (2), ben.boeckel (1), timothee.chabat (1), lucas.givord (1), spiros.tsalikis (1)
- [!13027](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13027) spiros.tsalikis, 2026-03-18: "i would appreciate if you could split this one commit to as many distinct as possible. this will help me in the review process."
- [!10816](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10816) lucas.givord, 2024-01-16: "Ideally, the commits should be reworked logically if they can. The historics of developpement does not matter but splitting logically is indeed beneficial."
- [!9821](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9821) timothee.chabat, 2023-01-06: "just a quick note for future MRs : I know sometimes it is a bit annoying but it's easier for reviewers if "refactoring" commits and "feature" commits are seperated, especially when there is -1000 +100"

### R067: To merge a merge request, add a comment containing only the text 'Do: merge'.

Rationale: The bots track the 'Do: merge' comment and perform additional checks before merging, which cannot be done by using the greyed-out green Merge button directly.

- Scope: merge requests
- Support: 6 MRs, 6 threads, 2017-12-21 to 2021-01-04
- Reviewers: cory.quammen (2), dcthomp (1), acbauer (1), sebastien.jourdain (1), ken-martin (1)
- [!7491](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7491) cory.quammen, 2021-01-04: "the merge command is `Do: merge`. We usually leave it to the MR author to merge in case you decide more changes are needed or want to withdraw the merge request."
- [!6565](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6565) cory.quammen, 2020-03-19: "Actually, will defer the merge to you @boonth. To merge, just write a comment with `Do: merge` on the last line (not sure if you've merged before, but you should have permission)."
- [!5539](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5539) ken-martin, 2019-05-23: "You can merge by adding a comment with "Do: merge" in it"

### R074: When merging after pushing new commits or rebasing/squashing, add a `Reviewed-by:` or `Acked-by:` line with the reviewer's handle (e.g., `Reviewed-by: @user`) in the merge comment or prior to the `Do: merge` line.

- Scope: merge comments and git history for merge commits
- Support: 6 MRs, 6 threads, 2019-09-26 to 2023-09-12
- Reviewers: cory.quammen (2), mwestphal (2), spiros.tsalikis (1), louis.gombert (1)
- [!10490](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10490) louis.gombert, 2023-09-12: "you need to have new line between each reviewed-by and do merge"
- [!10488](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10488) mwestphal, 2023-09-11: "As documented in the guide, please use the `Reviewed-by` syntax when merging after a push without a reconfirmation of the reviewer."
- [!10463](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10463) mwestphal, 2023-09-04: "use the Reviewed-by/Acked-by syntax when merging after a push, as documented in the guide"

### R089: Cherry-pick or rebase commits onto the release branch before creating a merge request targeting the release branch.

- Scope: unspecified
- Support: 5 MRs, 5 threads, 2016-06-29 to 2019-08-01
- Reviewers: sankhesh (2), utkarsh.ayachit (1), chuck.atkins (1), cory.quammen (1)
- [!5812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5812) cory.quammen, 2019-08-01: "Then, when you create your MR, change the target branch from `vtk/vtk` `master` to `vtk/vtk` `paraview/release`."
- [!2918](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2918) sankhesh, 2017-06-16: "Please rebase / cherry-pick changes onto the release branch and create a merge request to get these changes into 8.0."
- [!2925](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2925) sankhesh, 2017-06-16: "Please rebase / cherry-pick changes onto the release branch and create a merge request to get these changes into 8.0."

### R100: Ensure CI/CD is enabled and functioning correctly on your fork by deleting stale pipelines, unprotecting branches, rebasing on master, force pushing, and re-enabling CI/CD if disabled.

- Scope: forks used for merge requests
- Support: 5 MRs, 5 threads, 2021-08-05 to 2026-04-16
- Reviewers: mwestphal (4), ben.boeckel (1)
- [!13017](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13017) ben.boeckel, 2026-04-16: "There's a pipeline on your fork for the commit: https://gitlab.kitware.com/cory.quammen/vtk/-/pipelines/490834 Delete that pipeline and it should be fine."
- [!12224](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12224) mwestphal, 2025-06-20: "Please fix your CI: https://discourse.vtk.org/t/the-ultimate-how-to-make-ci-work-with-my-fork-guide/7581"
- [!10962](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10962) mwestphal, 2024-04-29: "please unprotected your branch, rebase on master, force push and follow this guide for correct CI"

### R119: Work must be done in a dedicated topic branch, not directly on the master branch.

Rationale: This ensures that test results will be a more reliable indicator of the test results once your branch is merged.

- Scope: unspecified
- Support: 4 MRs, 4 threads, 2017-07-12 to 2024-01-19
- Reviewers: cory.quammen (1), demarle (1), dgobbi (1), mwestphal (1)
- [!10831](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10831) mwestphal, 2024-01-19: "Please push to a dedicated branch on your fork instead of pushing to your master."
- [!5876](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5876) dgobbi, 2019-08-19: "Can you put the fix in a topic branch, instead of the master branch? This will require creating a new merge request, unfortunately."
- [!3228](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3228) demarle, 2017-09-04: "Michal you should checkout -b some-other-topic-name (or similar) instead of working directly off of your master branch with VTK."

### R138: Request a bypass token by commenting @utils/maintainers/bypass-vtk-vtk on the MR only when builds fail and merging despite CI failures is justified (e.g., unrelated failures, release branch rebase, or CI passed on release branch)

- Scope: Merge requests where build jobs fail
- Support: 4 MRs, 4 threads, 2025-05-13 to 2026-09-02
- Reviewers: vbolea (2), cory.quammen (1), mwestphal (1)
- [!13658](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13658) mwestphal, 2026-09-02: "If you feel the failure is unrelated to your changes and beyond your control, you can request a bypass token by adding a comment to your MR with the `@utils/maintainers/bypass-vtk-vtk`. Once the bypas"
- [!13016](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13016) cory.quammen, 2026-03-18: "FYI @berkgeveci you only need a bypass token if any **builds** fail and you have a good reason to merge anyway, not if any **tests** fail. So in this MR you wouldn't need one because you only had fail"
- [!12814](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12814) vbolea, 2026-01-16: "the release branch has been updated and I had to rebase this MR, can I have a bypass token to avoid running the CI again, note that the top of release branch passed CI correctly"

### R147: Merge requests must be rebased on master before testing to ensure the branch is tested as-is, not as if merged.

Rationale: Because CI tests the branch as-is, not as if it were merged, and using `--merged` during testing avoids failures from outdated branches and dashboard slowdowns.

- Scope: Merge request testing and CI
- Support: 3 MRs, 3 threads, 2020-05-20 to 2025-12-16
- Reviewers: utkarsh.ayachit (1), seanm (1), mwestphal (1)
- [!12699](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12699) mwestphal, 2025-12-16: "Usual MR that was not rebased on a change in master. Keep in mind we test the branch, not the branch as if it was merged."
- [!10389](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10389) seanm, 2023-08-03: "Testing is required on every mr before the merge."
- [!6908](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6908) utkarsh.ayachit, 2020-05-20: "When testing MRs, our dashboards do incremental builds by default (unless `Do: test --clean` is specified) to keep the build times down. When testing such branches that are not off a fairly new `maste"

### R151: Only the `quick` and `build` stages must pass to merge; failures in the `test` stage are acceptable if unrelated.

*Mixed evidence: check the examples before accepting.*

- Scope: CI pipeline stages (`quick`, `build`, `test`)
- Support: 3 MRs, 3 threads, 2024-06-03 to 2026-04-15
- Reviewers: seanm (1), scott.wittenburg (1), jaswant.panchumarti (1)
- [!13117](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13117) jaswant.panchumarti, 2026-04-15: "No. `quick` and `build` stages have run successfully. A job in the `test` stage failed but that failure is unrelated. Nevertheless, in order to merge, only the `quick` and `build` stage should pass an"
- [!11938](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11938) scott.wittenburg, 2025-05-08: "There is no requirement for all tests to pass to merge in VTK. Builds must pass, but not tests."
- [!11085](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11085) seanm, 2024-06-03: "Only builds are required to pass prior to merging. You can merge with a failing test."
- Counter-evidence:
  - [!9805](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9805) cory.quammen, 2023-01-16: "Since the VTK community has decided all builds must pass before merging, we will run into this situation from time to time."

### R167: When fixing ParaView issues in VTK, use 'addresses #ParaviewIssueNumber' or 'addresses paraview/...' in the commit message or MR description.

Rationale: To prevent GitLab from automatically closing the ParaView issue upon merging the VTK MR, since the issue is not truly fixed until ParaView updates its VTK.

- Scope: VTK MRs and commit messages that reference ParaView issues
- Support: 3 MRs, 3 threads, 2017-05-05 to 2025-08-06
- Reviewers: utkarsh.ayachit (2), jaswant.panchumarti (1)
- [!12343](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12343) jaswant.panchumarti, 2025-08-06: "When fixing ParaView issues in VTK, please use "address #ParaviewIssueNumber" or similar in the VTK MR commit message/description to mention that it is related to the ParaView issue. That is sufficien"
- [!8994](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8994) utkarsh.ayachit, 2022-03-15: "when creating VTK mr's, always use `addresses #<paraview issue>` rather than `closes ..` or `fixes ...`. Otherwise gitlab ends up closing the ParaVIew issue as soon as this is merged in VTK. That is n"
- [!2780](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2780) utkarsh.ayachit, 2017-05-05: "I often use `addresses paraview/...` text on commit messages for VTK commits that fix ParaView issues. That way, merging the commit won't automatically close the ParaView issue, since we still need to"

### R178: Check the dashboard after merging to ensure no warnings or errors appear on additional platforms.

Rationale: Despite all MR testing, it is common for additional platforms and associated tests to show up errors, and failing to check the dashboard the next day drives other developers crazy.

- Scope: unspecified
- Support: 3 MRs, 3 threads, 2018-09-14 to 2022-05-21
- Reviewers: demarle (1), will.schroeder (1), mwestphal (1)
- [!8957](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8957) mwestphal, 2022-05-21: "https://open.cdash.org/viewBuildError.php?type=1&buildid=7925491 C:\glr\builds\vtk\vtk-ci\Filters\Core\vtkPointDataToCellData.cxx(368): warning C4101: 'cellId': unreferenced local variable C:\glr\buil"
- [!5102](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5102) will.schroeder, 2019-01-30: "Whoever does it, make sure that you check the dashboard the next day after the merge. Despite all of the MR testing it is quite common for the additional platforms and associated tests to show up erro"
- [!4635](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4635) demarle, 2018-09-14: "do not merge any change without getting a plus one comment from a reviewer and check the dashboards the day after you merge to see if the wider set of nightly machines turned up anything that needs to"

### R207: Backport changes to the release branch if the intent is to include them in a patch release (e.g., 9.2, 9.3.1, 9.5.1)

- Scope: unspecified
- Support: 3 MRs, 3 threads, 2022-08-09 to 2025-08-18
- Reviewers: mwestphal (2), dgobbi (1)
- [!10752](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10752) dgobbi, 2025-08-18: "LGTM, but needs "Backport: release" if the intent is to get it into 9.5.1"
- [!10819](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10819) mwestphal, 2024-01-11: "9.3.0 is out already, but fixes should be backported to release for a potential 9.3.1"
- [!9467](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9467) mwestphal, 2022-08-09: "you need to rebase on release to be able to get this in 9.2"

### R213: Comment `Do: test` to trigger CI

- Scope: merge request reviews
- Support: 3 MRs, 3 threads, 2024-02-16 to 2025-06-13
- Reviewers: thomas.galland (1), jaswant.panchumarti (1), mwestphal (1)
- [!12208](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12208) mwestphal, 2025-06-13: "and finally, please prefer using `Do: test` to trigger CI :)"
- [!10924](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10924) jaswant.panchumarti, 2024-02-28: "You can run the CI by commenting `Do: test` without the backticks."
- [!10850](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10850) thomas.galland, 2024-02-16: "Please also run the CI when it's done by using the `Do: test` command, to check everything is fine"

### R215: Skip non-macOS CI for merge requests that only affect Windows-only features or are unrelated to macOS.

- Scope: CI pipelines for non-macOS platforms
- Support: 3 MRs, 3 threads, 2024-06-14 to 2026-01-09
- Reviewers: vbolea (1), ben.boeckel (1), mathurin.lemarie (1)
- [!11228](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11228) ben.boeckel, 2024-06-14: "We don't need to run non-macOS (arm64 can be skipped too) CI for this; will get a bypass token once the update is made."
- [!12710](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12710) mathurin.lemarie, 2026-01-09: "Def not."
- [!10973](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10973) vbolea, 2024-08-01: "^VTK::RenderingCellGridPython-TestCellGridRendering$"

## deprecation-abi

### R002: Use the VTK_DEPRECATED_IN_X_Y_Z macro (e.g., VTK_DEPRECATED_IN_9_6_0) on deprecated methods, optionally with a descriptive message, and include vtkDeprecation.h where used.

*Mixed evidence: check the examples before accepting.*

- Scope: C++ source files (.cxx, .h)
- Support: 31 MRs, 35 threads, 2015-11-06 to 2026-04-27
- Reviewers: mwestphal (10), ben.boeckel (9), utkarsh.ayachit (4), charles.gueunet (2), spiros.tsalikis (2)
- [!13163](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13163) corentin.munoz, 2026-04-27: "Why not using the VTK_DEPRECATED macro ?"
- [!12564](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12564) mwestphal, 2026-02-13: "#include "vtkDeprecation.h" // For VTK_DEPRECATED_IN_9_6_0()"
- [!12578](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12578) mwestphal, 2025-12-01: "VTK_DEPRECATED_IN_9_6_0("This method is deprecated, use the other version instead")"
- Counter-evidence:
  - [!3600](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3600) jpouderoux, 2017-11-20: "Use `VTK_LEGACY_REPLACED_BODY` instead."
  - [!7754](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7754) ben.boeckel, 2021-03-16: "Hide VTK_DEPRECATED_IN_9_1_0() warnings for this class. #define VTK_DEPRECATION_LEVEL 0"

### R017: VTK_ABI_NAMESPACE_BEGIN and VTK_ABI_NAMESPACE_END must wrap all class declarations, forward declarations, and C-linkage symbols in new files to ensure ABI compatibility.

- Scope: new files containing class declarations, forward declarations, or C-linkage symbols
- Support: 14 MRs, 15 threads, 2022-10-13 to 2026-06-30
- Reviewers: lucas.givord (4), ben.boeckel (3), mwestphal (2), ryan.krattiger1 (1), thomas.galland (1)
- [!13361](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13361) lucas.givord, 2026-06-30: "abi namespace begin/end in this file are missing"
- [!13100](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13100) lucas.givord, 2026-04-02: "we need it in the abi namespace (VTK_ABI_NAMESPACE_BEGIN) right ?"
- [!12221](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12221) jaswant.panchumarti, 2025-11-16: "I think the practice is to use `VTK_ABI_NAMESPACE_MANGLE` for symbols with C linkage."

### R019: Deprecated methods must include a deprecation message that directs users to the replacement method(s) and, if applicable, explains why the method is deprecated (e.g., no longer used, replaced by a new method).

*Mixed evidence: check the examples before accepting.*

- Scope: C++ source code
- Support: 13 MRs, 19 threads, 2022-04-06 to 2026-09-17
- Reviewers: mwestphal (5), dgobbi (5), charles.gueunet (1), cory.quammen (1), thomas.galland (1)
- [!13025](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13025) dgobbi, 2026-03-16: "VTK_DEPRECATED_IN_9_7_0("Use ReserveValues/Tuples() to allocate or Initialize() to deallocate.")"
- [!12949](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12949) spiros.tsalikis, 2026-03-03: "Then yes, each renamed/replaced method should be deprecated."
- [!12464](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12464) timothee.couble, 2025-09-16: "Should the old methods be deprecated @mwestphal? Yes, see https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8262/diffs#3ca99774cc16574f697fd6c7b48b4a668a4cd3f0"
- Counter-evidence:
  - [!11988](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11988) mwestphal, 2025-04-03: "it is used by a deprecated method. I added a DEPREC comment here to remove them alongside with the call."
  - [!12906](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12906) cory.quammen, 2026-03-12: "this is to help the maintainers who will remove the deprecation in two minor versions."

### R025: Deprecate public APIs (classes, functions, methods, enums, parameters, types) before removing or changing them to avoid breaking existing code.

Rationale: To avoid breaking existing code and maintain retrocompatibility.

- Scope: public APIs (classes, functions, methods, enums, parameters, types)
- Support: 12 MRs, 14 threads, 2019-07-29 to 2026-07-20
- Reviewers: mwestphal (4), spiros.tsalikis (4), jpouderoux (1), ben.boeckel (1), drpeterfranz (1)
- [!13406](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13406) lucas.gottar, 2026-07-20: "true, old version needs to be deprecacted"
- [!13098](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13098) cory.quammen, 2026-05-05: "This is an API break with no deprecation, no?"
- [!12889](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12889) spiros.tsalikis, 2026-02-05: "This needs to be deprecated... you can't just remove it. It's a bad idea to remove this function."

### R079: API breaks or changes must be documented in a release note.

- Scope: unspecified
- Support: 6 MRs, 6 threads, 2021-05-29 to 2026-06-08
- Reviewers: ben.boeckel (4), mwestphal (1), acbauer (1)
- [!13311](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13311) ben.boeckel, 2026-06-08: "Technically an API break, but it feels pretty benign to me; I think a release note is still warranted to at least give a heads up."
- [!12746](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12746) ben.boeckel, 2025-12-26: "Release notes mentioning the removed APIs should be added."
- [!8832](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8832) ben.boeckel, 2022-03-04: "There are some API changes here, but they're not documented in the release note."

### R080: Deprecate protected methods and data members when changing or removing them.

Rationale: Protected members need deprecation because external code may reimplement or depend on them, and there is no proper way to deprecate a protected member directly—accessors are required for data members to enable deprecation.

- Scope: C++ protected methods and data members
- Support: 6 MRs, 7 threads, 2024-02-26 to 2026-02-13
- Reviewers: mwestphal (3), lucas.givord (2), nicolas.vuaille (1), spiros.tsalikis (1)
- [!12918](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12918) lucas.givord, 2026-02-13: "I don't remember, can we deprecate a protected members ?"
- [!12321](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12321) spiros.tsalikis, 2025-12-10: "I don't like what i am gonna say... but, you need to deprecate the old ones... and add new ones since they are protected and not private. Do the same for all subclasses."
- [!11725](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11725) lucas.givord, 2024-12-04: "I think that it is in the 9.4.0 and as it's a protected method we need to deprecate it"

### R086: Update deprecation macros to use the version number of the release in which the deprecation is intended to take effect.

- Scope: C++ source files using deprecation macros
- Support: 5 MRs, 6 threads, 2021-11-30 to 2026-08-03
- Reviewers: spiros.tsalikis (2), tiffany.chhim (1), ben.boeckel (1), cory.quammen (1), louis.gombert (1)
- [!13536](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13536) louis.gombert, 2026-08-03: "If we do, can we please migrate to something that doesn't inject global ctors into all consumers (like the reverted patch here)? indeed, deprecation needed first."
- [!11639](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11639) cory.quammen, 2024-11-14: "Since this won't go in 9.4, this should be VTK_DEPRECATED_IN_9_5_0, right?"
- [!9812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9812) spiros.tsalikis, 2023-12-12: "Change VTK_DEPRECATED_IN_9_3_0 -> VTK_DEPRECATED_IN_9_4_0"

### R098: Deprecate old APIs before removing or changing them to avoid breaking existing applications/builds.

Rationale: Removing or changing deprecated APIs without a ramp breaks applications/builds that still use the old/deprecated API.

- Scope: C++ public APIs
- Support: 5 MRs, 6 threads, 2020-09-29 to 2026-01-14
- Reviewers: cory.quammen (1), yohann.bearzi (1), spiros.tsalikis (1), mwestphal (1), demarle (1)
- [!9812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9812) spiros.tsalikis, 2023-10-13: "IMO, this function should not exist. You should not encourage people using the old format, you can keep it as a private function and deprecate so that it is removed when the legacy face locations are "
- [!10165](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10165) demarle, 2023-05-18: "I suggest leave the old string in and simply override both. There is no harm in leaving the old "..2" string here. Applications/builds that use the new CPDM will simply not exercise it and removing wi"
- [!10029](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10029) mwestphal, 2023-03-08: "this is an API change. you need to deprecate previous API"

### R103: Replace VTK_OVERRIDE with the C++11 override keyword

*Mixed evidence: check the examples before accepting.*

Rationale: A C++11 compiler is required, making the VTK_OVERRIDE macro obsolete

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2017-06-08 to 2018-12-04
- Reviewers: jpouderoux (2), robertmaynard (1), demarle (1)
- [!1455](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1455) robertmaynard, 2018-12-04: "Note `VTK_OVERRIDE` is going to be removed ( placed behind VTK_LEGACY_REMOVE ) as a C++11 compiler is required."
- [!3647](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3647) jpouderoux, 2017-12-04: "VTK_OVERRIDE keyword is deprecated, use `override` instead"
- [!3308](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3308) demarle, 2017-10-13: "replace VTK_OVERRIDE with override (a recent VTK change obsoleted the macro since we no longer need c++97 compatibility)"
- Counter-evidence:
  - [!1894](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1894) utkarsh.ayachit, 2016-09-07: "Use `VTK_OVERRIDE` and remove `virtual` for new classes."
  - [!2872](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2872) jpouderoux, 2017-05-24: "Remove `virtual`keyword and add `VTK_OVERRIDE` at the end of the prototype declaration (see C++11 related rules)"
  - [!2917](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2917) demarle, 2017-06-07: "This needs VTK_OVERRIDE because c++11 constructs are now required."

### R150: Remove deprecated functions once replacement functions are provided and macros are active.

*Mixed evidence: check the examples before accepting.*

Rationale: To guide users toward updated APIs and ensure deprecated functions are cleaned up once the deprecation mechanism is active.

- Scope: C++ source code (specifically functions marked as deprecated with replacement functions and macros)
- Support: 3 MRs, 3 threads, 2021-10-04 to 2026-01-29
- Reviewers: tiffany.chhim (1), spiros.tsalikis (1), louis.gombert (1)
- [!12844](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12844) louis.gombert, 2026-01-29: "vtkHDFUtilities::RetrieveHDFInformation has been deprecated in favor of a version with more arguments."
- [!9812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9812) spiros.tsalikis, 2023-10-13: "Deprecate these 2 functions since you have 2 new ones, and you would like users to use the new ones."
- [!8471](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8471) tiffany.chhim, 2021-10-04: "Yes, once the macros were actually active, that MR fixed things. It should already have been included here though, no?"
- Counter-evidence:
  - [!9812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9812) spiros.tsalikis, 2023-10-13: "The new GetFaces is not introduced anymore as GetFaces is a deprecated function."

### R152: Deprecate the previous method when adding a new overload.

Rationale: to avoid confusion with new overloads

- Scope: C++ method overloads
- Support: 3 MRs, 3 threads, 2023-03-08 to 2026-09-17
- Reviewers: mwestphal (2), louis.gombert (1)
- [!13678](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13678) louis.gombert, 2026-09-17: "deprec and redirect to the other overload"
- [!12452](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12452) mwestphal, 2025-10-01: "because otherwise in vtkUnstructuredGrid, you will have `vtkDataArray* GetCellTypes();` `void GetCellTypes(vtkCellTypes* types)` In my opinion, that would be confusing."
- [!10026](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10026) mwestphal, 2023-03-08: "you need to deprecate the previous method."

### R194: Use GetPointer instead of GetVoidPointer.

Rationale: GetVoidPointer is to be deprecated in favor of GetPointer for AOS arrays of known types, and array dispatch should be used instead for general cases.

- Scope: C++ sources (filters and general code using VTK data arrays)
- Support: 3 MRs, 3 threads, 2020-06-10 to 2026-07-17
- Reviewers: sankhesh (1), mwestphal (1), spiros.tsalikis (1)
- [!13465](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13465) spiros.tsalikis, 2026-07-17: "Don't use GetVoidPointer. Use GetPointer."
- [!9631](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9631) mwestphal, 2022-10-16: "The right way to fix this issue is to deprecate GetVoidPointer() and use array dispatch. Nonetheless, it's important for SOA to properly work. So, either we go for a temporary solution like this, or w"
- [!6983](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6983) sankhesh, 2020-06-10: "Removes use of GetVoidPointer which is to be deprecated as described in https://blog.kitware.com/working-with-vtkdataarrays-2019-edition/"

### R209: Files linked publicly in CMake code must include the ABI namespace macro for their public API.

- Scope: C++ source files linked publicly in CMake code
- Support: 3 MRs, 3 threads, 2023-02-23 to 2026-04-02
- Reviewers: charles.gueunet (2), lucas.givord (1)
- [!13100](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13100) lucas.givord, 2026-04-02: "as this file is linked publicly in the cmake code, we need the abi namespace macro in this file"
- [!10762](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10762) charles.gueunet, 2024-01-05: "those should be in the ABI NAMESPACE"
- [!9807](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9807) charles.gueunet, 2023-02-23: "no `VTK_ABI_NAMESPACE_BEGIN` ?"

### R217: Move deprecated class implementations to the header file if deprecating both the class and its parent to avoid compile-time warnings, or move implementation to the .cxx file if deprecating inline functions to avoid warnings.

Rationale: To avoid compile-time warnings when deprecating classes or inline functions.

- Scope: C++ source files (.h and .cxx) for deprecated classes and inline functions
- Support: 3 MRs, 3 threads, 2024-10-11 to 2026-02-16
- Reviewers: ben.boeckel (1), cory.quammen (1), lucas.givord (1)
- [!12924](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12924) lucas.givord, 2026-02-16: "should be in the header"
- [!12564](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12564) cory.quammen, 2026-02-06: "So that i can avoid getting a warning at compile time because i deprecate both itself and its parent."
- [!11558](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11558) ben.boeckel, 2024-10-11: "Please move the implementation to the `.cxx` (the `inline`-ness triggers warnings when it is deprecated)"

## memory-ownership

### R005: Use vtkNew for VTK object creation and smart pointer declarations.

*Mixed evidence: check the examples before accepting.*

Rationale: to avoid memory leaks and manual memory management (e.g., ->Delete() + nullptr)

- Scope: C++ sources
- Support: 25 MRs, 37 threads, 2015-08-21 to 2021-03-22
- Reviewers: mwestphal (8), utkarsh.ayachit (8), jpouderoux (5), michael.migliore (4), mhanwell (3)
- [!6016](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6016) utkarsh.ayachit, 2019-10-09: "this, I suspect is the leak. Note type of `auto outputMBDS` is `vtkMultiBlockDataSet` and not `vtkSmartPointer<vtkMultiBlockDataSet>`. I'd change it to not be `auto` instead be `vtkSmartPointer<vtkMul"
- [!5439](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5439) jpouderoux, 2019-04-18: "vtkNew would be shorter here"
- [!5261](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5261) amaclean, 2019-03-04: "Personally I would prefer `vtkNew`, in this case, as it makes the code neater and easier to read."
- Counter-evidence:
  - [!1845](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1845) msmolens, 2016-08-19: "Note: Objects of subclasses of vtkObjectBase should always be created with the New() method and deleted with the Delete() method. They cannot be allocated off the stack (i.e., automatic objects) becau"
  - [!4707](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4707) jpouderoux, 2018-09-26: "again, avoid vtknew and PassData"

### R038: Use smart pointers (e.g., vtkSmartPointer, unique_ptr) to avoid manual Delete() or delete calls.

- Scope: C++ sources
- Support: 9 MRs, 10 threads, 2016-12-06 to 2026-03-25
- Reviewers: mwestphal (3), michael.migliore (2), charles.gueunet (2), jpouderoux (1), will.schroeder (1)
- [!13052](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13052) mwestphal, 2026-03-25: "its a smart pointer now, not needed anymore."
- [!12132](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12132) louis.gombert, 2025-05-20: "you should not need to delete a smart pointer manually. Use TakeSmartPointer or equivalent"
- [!10552](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10552) charles.gueunet, 2023-10-02: "`unique_ptr` ? We need to avoid explicit call to `->delete` at the end."

### R042: Use vtkWeakPointer for non-owning references to VTK objects to avoid dangling pointers and cyclic dependencies.

Rationale: To prevent dangling pointers when referenced objects may be deleted and to avoid cyclic dependencies that cause leaks.

- Scope: C++ sources
- Support: 8 MRs, 8 threads, 2017-06-01 to 2026-08-17
- Reviewers: sankhesh (3), jpouderoux (1), cory.quammen (1), charles.gueunet (1), mwestphal (1)
- [!13574](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13574) sankhesh, 2026-08-17: "This has the potential to become a dangling pointer if all cullers are removed from the renderer. Use `vtkWeakPointer<vtkCuller>` instead."
- [!13359](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13359) finetjul, 2026-07-08: "You do not want vtkQuadricDecimation to "prevent" the deletion of "input" though. So you can use a vtkWeakPointer or a raw pointer (if you reset to null when you no longer need it)"
- [!13327](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13327) sankhesh, 2026-06-11: "Consider making this a vtkWeakPointer"

### R049: Use smart pointers for member variables and memory management.

*Mixed evidence: check the examples before accepting.*

Rationale: to avoid deep copying and manage memory automatically

- Scope: C++ code
- Support: 7 MRs, 7 threads, 2017-06-09 to 2025-03-27
- Reviewers: mwestphal (3), jpouderoux (2), julien.fausty (1), lucas.givord (1)
- [!11986](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11986) mwestphal, 2025-03-27: "you should be able to swap without deepcopying anything. If you keep smart pointers to the arrays, they should not be deallocated when calling SetCoord"
- [!10310](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10310) lucas.givord, 2023-07-03: "could be a smart ptr"
- [!9710](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9710) julien.fausty, 2022-12-02: "smart pointer here would be better"
- Counter-evidence:
  - [!5439](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5439) jpouderoux, 2019-04-18: "smartpointers are useless here"
  - [!10197](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10197) julien.fausty, 2023-05-22: "IMO this should be a weak pointer and not a smart pointer"
  - [!13359](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13359) finetjul, 2026-09-09: "don't bother using a smart pointer here"

### R052: Use std::vector instead of raw arrays with manual memory management (e.g., new/delete, memset, manual reallocation).

Rationale: to avoid memory leaks, simplify code, and avoid manual memory management

- Scope: C++ source code
- Support: 7 MRs, 7 threads, 2016-04-03 to 2024-03-28
- Reviewers: acbauer (1), jpouderoux (1), michael.migliore (1), cory.quammen (1), timothee.chabat (1)
- [!11001](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11001) louis.gombert, 2024-03-28: "use std::vector/std::array ? same for facePoints where it can simplify init yes, much better"
- [!10609](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10609) charles.gueunet, 2023-10-23: "you should be able to build this vector with `std::begin(cellOrigin)` and `std::end(cellOrigin)` to avoid the `memcpy` (here and below)"
- [!9912](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9912) timothee.chabat, 2023-02-13: "`std::vector<double[3]>` or `std::vector<std::array<double, 3>>`, but not a vector of heap-allocated doubles that you need to delete`"

### R054: Use vtkCxxSetObjectMacro for VTK object pointers in implementation files to ensure proper reference counting and avoid memory leaks or dangling pointers.

Rationale: Otherwise the controller instance is not freed and it creates memory leaks, or it leads to dangling pointer if the generator is deleted.

- Scope: implementation files (e.g., .cxx files)
- Support: 7 MRs, 7 threads, 2016-11-03 to 2025-09-08
- Reviewers: mwestphal (4), aashish-chaudhary (1), dgobbi (1), jpouderoux (1)
- [!12428](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12428) mwestphal, 2025-09-08: "you can use macros for all of these, see vtkCxxSetSmartPointerMacro"
- [!11842](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11842) mwestphal, 2025-01-15: "it is, otherwise the controller instance is not freed and it creates memory leaks"
- [!8618](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8618) mwestphal, 2021-11-18: "use vtkCxxSetObjectMacro in implementation instead."

### R063: Configure VTK with VTK_DEBUG_LEAKS=ON to detect memory leaks of VTK objects.

- Scope: tests and code using VTK objects (specifically where New()/Delete() or smart pointers are used)
- Support: 6 MRs, 6 threads, 2017-01-16 to 2022-07-07
- Reviewers: demarle (3), sujin.philip (1), mwestphal (1), timothee.chabat (1)
- [!9363](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9363) timothee.chabat, 2022-07-07: "please compile with `VTK_DEBUG_LEAKS=ON` to be sure there is no leak when using this reader"
- [!6231](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6231) demarle, 2019-11-26: "If you turn on VTK_DEBUG_LEAKS in your cmake configuration and rebuild VTK you can reproduce the leak that is causing the PIO test to fail."
- [!4271](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4271) demarle, 2018-10-23: "The python tests (ctest -R Python-Quadric) are leaking with this change. I suspect your New needs to be Delete'd or put in a smartpointer I think. Make sure you configure VTK with VTK_DEBUG_LEAKS on t"

### R081: Call reserve() on vectors when the number of elements is known or approximately known before populating the vector.

*Mixed evidence: check the examples before accepting.*

Rationale: To avoid reallocations and copies by pre-allocating memory once.

- Scope: C++ code using std::vector
- Support: 5 MRs, 5 threads, 2017-05-06 to 2025-07-01
- Reviewers: charles.gueunet (2), utkarsh.ayachit (1), timothee.chabat (1), mathurin.lemarie (1)
- [!12185](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12185) mathurin.lemarie, 2025-07-01: "I don't know how many elements is in this vector, but using `reserve` before iterating with `emplace_back` will allocate the memory needed to the vector once. as you already know the size (`this->Inte"
- [!10355](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10355) charles.gueunet, 2023-08-24: "With just the change that in a distributed context it is `pieces.reserve(filePieceCount/memoryPieceCount)`"
- [!9821](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9821) timothee.chabat, 2023-01-06: "if you have an approximate idea of the number of elements in these vectors you can call `reserve` to avoid some copy and memory allocation"
- Counter-evidence:
  - [!8667](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8667) will.schroeder, 2021-11-23: "On some rare systems I have seen reserve() not actually allocate memory. Later on you are using std::copy() which may presume that memory has been properly allocated (I can't quite remember if this is"

### R091: Use `vtkIdType` when accessing raw pointers or when compatibility across 32-bit and 64-bit builds is required; otherwise, use `vtkTypeInt64` or `vtkTypeInt32` based on dataset size and build configuration (`VTK_USE_64BIT_IDS`).

Rationale: To ensure correct integer size handling for IDs across 32-bit and 64-bit builds, avoid overflow in calculations, and maintain compatibility with raw pointer access.

- Scope: C++ sources
- Support: 5 MRs, 5 threads, 2017-08-07 to 2025-04-18
- Reviewers: spiros.tsalikis (2), jpouderoux (1), seanm (1), jaswant.panchumarti (1)
- [!12012](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12012) jaswant.panchumarti, 2025-04-18: "Use `vtkIdType` which can fit 64-bit integers when building for 64-bit."
- [!10769](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10769) spiros.tsalikis, 2023-12-30: "Unless something has changed, sharable means that you can access the raw vtkIdType pointer. So for both 32 and 64 bits you need to compare with vtkIdType and not vtkTypeInt32 or vtkTypeInt64."
- [!9977](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9977) seanm, 2023-02-17: "bool use64BitsIds = (dataSetInput->GetNumberOfPoints() > VTK_TYPE_INT32_MAX || dataSetInput->GetNumberOfCells() > VTK_TYPE_INT32_MAX);"

### R102: Avoid using smart pointers when raw pointers suffice, especially for local variables and stored members.

*Mixed evidence: check the examples before accepting.*

Rationale: Implicit cast of smart pointer rvalues to raw pointers is disabled to prevent memory leaks.

- Scope: C++ code
- Support: 4 MRs, 4 threads, 2018-05-31 to 2021-10-04
- Reviewers: LucasGandelKitware (1), lassoan (1), michael.migliore (1), mwestphal (1)
- [!8469](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8469) mwestphal, 2021-10-04: "you could take that out of the if and avoid the smart pointer."
- [!6212](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6212) michael.migliore, 2019-11-20: "you can safely use a raw pointer here"
- [!5308](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5308) lassoan, 2019-03-25: "This change causes a few build failures in Slicer, too, but they are easy to fix and it prevents this incorrect usage of the API (which causes memory leaks): vtkSmartPointer<vtkDoubleArray> data = vtk"
- Counter-evidence:
  - [!10022](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10022) lucas.givord, 2023-03-06: "avoid raw pointer if possible"
  - [!12311](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12311) lucas.givord, 2025-10-22: "avoid raw pointer if it's possible"
  - [!13167](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13167) spiros.tsalikis, 2026-04-24: "Although i would highly recomend using std::unique_ptr instead of raw pointers."

### R104: Use `delete[]` (without space) for arrays allocated with `new[]`.

*Mixed evidence: check the examples before accepting.*

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2017-05-29 to 2023-03-24
- Reviewers: mwestphal (2), cory.quammen (1), dgobbi (1)
- [!9956](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9956) mwestphal, 2023-02-15: "`delete[] this->Stack;` should be enough. No need to reset member, no need to check if allocated."
- [!8784](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8784) dgobbi, 2022-01-11: "The deleter needs `delete[]` to match the `new[]` in `vtk_Py_UTF8ToWide()`, since the strings aren't being created by Python APIs anymore."
- [!2882](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2882) mwestphal, 2017-05-29: "`delete []` -> `delete[]`"
- Counter-evidence:
  - [!1549](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1549) ben.boeckel, 2016-06-16: "It isn't checking to see if it's null, it's checking to see if it is equal to `Storage`. So `delete []` is called if it's null (which is a no-op) or if it was allocated with `new []`."
  - [!3552](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3552) utkarsh.ayachit, 2017-12-14: "should be `delete [] this->TranslationFactor`."

### R117: Memory allocated with `new` must be freed with `delete` and not with `free`, and allocations made with `New()` must be properly deallocated to avoid leaks, especially when code paths are duplicated.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2016-04-06 to 2021-11-18
- Reviewers: sankhesh (1), kmorel (1), jpouderoux (1), mwestphal (1)
- [!8618](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8618) mwestphal, 2021-11-18: "you need a delete"
- [!3941](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3941) jpouderoux, 2018-02-16: "you cannot `free` a pointer allocated with `new`"
- [!1883](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1883) kmorel, 2016-08-29: "It looks like these lines were copied from what is now on lines 1411-1412, but those lines were never deleted. This means it looks like `New` would be called twice when `VTK_DATASET_SURFACE_USE_510_AL"

### R121: Use std::unique_ptr for ownership of heap-allocated objects.

- Scope: C++ sources
- Support: 4 MRs, 5 threads, 2017-11-22 to 2023-11-15
- Reviewers: robertmaynard (1), michael.migliore (1), charles.gueunet (1), nicolas.vuaille (1), lucas.givord (1)
- [!10638](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10638) lucas.givord, 2023-11-15: "you will need to include `<memory>` to be able to use `std::unique_ptr`"
- [!9448](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9448) nicolas.vuaille, 2022-08-19: "may use a `unique_ptr` to avoid this"
- [!3610](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3610) robertmaynard, 2017-11-22: "this is should be std::unique_ptr. auto_ptr is deprecated in c++11"

### R145: Set pointers to nullptr after calling FastDelete or when resetting smart pointers instead of calling Delete() or deleting nullptr.

*Mixed evidence: check the examples before accepting.*

- Scope: C++ sources
- Support: 3 MRs, 4 threads, 2019-05-07 to 2022-05-02
- Reviewers: sebastien.jourdain (2), michael.migliore (1), mwestphal (1)
- [!9142](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9142) mwestphal, 2022-05-02: "not needed, you can delete nullptr fixed"
- [!5738](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5738) michael.migliore, 2019-07-11: "I would prefer `this->Locator = nullptr` if exposing the api is necessary"
- [!5485](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5485) sebastien.jourdain, 2019-05-07: "this->Points = nullptr; this->Cells = nullptr;"
- Counter-evidence:
  - [!10697](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10697) mwestphal, 2023-11-10: "this should not be needed, this does not exist after the destructor."

### R153: Use vtk::Range or vtkSmartPointer to manage VTK iterator objects and avoid manual memory management.

Rationale: To prevent memory leaks and avoid 'weird iterators' that are less safe or idiomatic.

- Scope: C++ sources using VTK iterators
- Support: 3 MRs, 3 threads, 2015-05-05 to 2025-11-24
- Reviewers: utkarsh.ayachit (1), louis.gombert (1), alexy.pellegrini (1)
- [!12640](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12640) alexy.pellegrini, 2025-11-24: "A good thing to do is maybe deprecate all the weird iterators in favor of vtk:Range."
- [!10983](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10983) louis.gombert, 2024-03-26: "yes, this untested filter used to leak memory"
- [!145](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/145) utkarsh.ayachit, 2015-05-05: "Iterator will leak. I'd suggest switching to using a smart pointer at line #442 (something as follows) and then removeing the iter->Delete() later in this function. vtkSmartPointer<vtkDataObjectTreeIt"

### R165: The caller must free memory allocated and returned by a function.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2017-06-06 to 2021-09-29
- Reviewers: jacob (1), jpouderoux (1), timothee.chabat (1)
- [!8457](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8457) timothee.chabat, 2021-09-29: "If you can please check for other use of `vtkOSPRayMaterialLibrary::WriteBuffer` an if thery are correctly freeing memory in other places of VTK. Also specify in the doc that users have to free the re"
- [!2915](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2915) jpouderoux, 2017-06-06: "It is caller's responsibility to delete it with the delete operator."
- [!2636](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2636) jacob, 2018-11-20: "delete [] filename;"

## naming

### R021: Member variables and member function names in classes/structs must start with an uppercase letter (PascalCase).

*Mixed evidence: check the examples before accepting.*

- Scope: C++ class/struct members
- Support: 12 MRs, 16 threads, 2016-03-08 to 2026-05-26
- Reviewers: spiros.tsalikis (5), cory.quammen (3), will.schroeder (1), jpouderoux (1), LucasGandelKitware (1)
- [!13105](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13105) spiros.tsalikis, 2026-05-26: "Class/Struct member variables are PascalCase, not scaneCase."
- [!11567](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11567) jaswant.panchumarti, 2024-12-03: "Convert member variables to `PascalCase` instead of `camelCase`"
- [!11247](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11247) cory.quammen, 2024-07-12: "I would capitalize these two member names."
- Counter-evidence:
  - [!4707](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4707) jpouderoux, 2018-09-26: "All members should be in CamelCase."

### R033: Use VTK naming conventions, including descriptive variable names, avoiding `vtk` prefix in variable names, using `vtki` for private implementations, abbreviating web graphics library names, and ensuring names remain valid identifiers without the `vtk` prefix.

- Scope: C++ sources
- Support: 10 MRs, 10 threads, 2017-11-22 to 2025-01-30
- Reviewers: cory.quammen (3), mwestphal (2), jpouderoux (1), ben.boeckel (1), utkarsh.ayachit (1)
- [!11884](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11884) mwestphal, 2025-01-30: "please rename this var"
- [!11352](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11352) cory.quammen, 2024-07-29: "This MR introduces some new conventions for naming in VTK, in particular abbreviating a web graphics library name and using `vtki` to indicate a private implementation."
- [!10587](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10587) thomas.galland, 2023-10-13: "maybe avoid using `vtk` prefix in variable names"

### R065: Use descriptive variable and function parameter names that reflect their purpose and context, avoiding single letters and unclear abbreviations, and following camelCase conventions.

- Scope: C++ sources
- Support: 6 MRs, 8 threads, 2017-08-18 to 2026-07-21
- Reviewers: jpouderoux (3), mwestphal (2), timothee.chabat (1), michael.migliore (1), finetjul (1)
- [!9126](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9126) timothee.chabat, 2022-04-26: "better naming (`shaderFunction', 'signature', 'shaderCode', ...')"
- [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) jpouderoux, 2020-03-27: "If swap has been done during reading step, is it a useful public information? At least var should be name "SwappedAxis" instead?"
- [!3127](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3127) mwestphal, 2017-09-12: "d is not a good variable name"

### R075: Use camelCase (or CamelCase) for naming.

- Scope: unspecified
- Support: 6 MRs, 6 threads, 2020-09-02 to 2025-11-28
- Reviewers: mwestphal (4), julien.fausty (1), mathurin.lemarie (1)
- [!12574](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12574) mathurin.lemarie, 2025-11-07: "All of this should stay in camel case"
- [!11678](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11678) mwestphal, 2024-11-18: "use camelCase in this file I think"
- [!12655](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12655) mwestphal, 2025-11-28: "worth camelCase"

### R078: Enum values must use explicit, all-caps names that are clear, descriptive, concise, consistent, and context-specific, and enum types should be singular to avoid implying bitwise combination.

- Scope: C++ enum definitions
- Support: 6 MRs, 6 threads, 2020-09-29 to 2026-03-05
- Reviewers: mwestphal (3), cory.quammen (1), julien.fausty (1), leon.victor (1)
- [!12714](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12714) mwestphal, 2026-03-05: "use explicit names for enums, in all caps."
- [!12611](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12611) mwestphal, 2025-11-18: "use better namings for your enums: eg: `INTER_STATE_OUTSIDE`"
- [!11358](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11358) leon.victor, 2024-08-01: "I think that enum name is not right. `IndexingMode::Points` would be clearer, maybe `IndexingMode::IndexedOnPoints` if you prefer"

### R085: Class names must not include the 'vtk' prefix in the class definition itself.

- Scope: C++ class definitions
- Support: 5 MRs, 5 threads, 2019-04-18 to 2026-03-25
- Reviewers: mwestphal (2), jpouderoux (1), michael.migliore (1), adam-grant-hendry (1)
- [!9443](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9443) adam-grant-hendry, 2022-08-08: "This should also be `SwipeGesture`, not `QSwipeGesture`"
- [!6959](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6959) mwestphal, 2020-06-01: "I like your proposal `QVTKRenderWidget` for the interface, but it should not have `Widget` or `Q` since that interface does no extend from `Widget` or `QObject`."
- [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) michael.migliore, 2020-03-06: "remove `vtk` prefix for class methods"

### R110: Function names should use camelCase with a lowercase first letter for parameters and local variables, and PascalCase (or CamelCase with uppercase first letter) for functions and members.

*Mixed evidence: check the examples before accepting.*

- Scope: C++ sources
- Support: 4 MRs, 5 threads, 2022-05-18 to 2024-03-28
- Reviewers: LucasGandelKitware (2), timothee.chabat (1), dcthomp (1), louis.gombert (1)
- [!11001](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11001) louis.gombert, 2024-03-28: "`AreAllFacesPlanar` would be a better name :smile:"
- [!10475](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10475) dcthomp, 2023-09-04: "`HideInternalCellBoundaries` should be `hideInternalCellBoundaries` (lowercase initial character for function parameters)."
- [!9602](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9602) LucasGandelKitware, 2023-01-09: "zccompatGetFrustumCameraOffset -> zccompatSetFrustumAttributeF32 ?"
- Counter-evidence:
  - [!8147](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8147) cory.quammen, 2021-07-15: "Please capitalize the `i` in `interpolateVector`"

### R116: Use full words instead of abbreviations in naming.

Rationale: It makes the code easier to read and is self-documenting without someone having to guess what it is short for.

- Scope: unspecified
- Support: 4 MRs, 4 threads, 2016-05-15 to 2026-08-25
- Reviewers: cory.quammen (3), lucas.givord (1)
- [!13500](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13500) lucas.givord, 2026-08-25: "I suppose u and v are edge indices ? And w the weight ? we should avoid, when it's possible, abbreviation for maintainability"
- [!10625](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10625) cory.quammen, 2023-10-23: "I'm a big advocate of spelling out the full word for code clarity to benefit future developers, so I'd lobby you to change "Ave" to "Average"."
- [!8595](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8595) cory.quammen, 2021-11-02: "In this case, prefer the full word over an abbreviation, e.g., `tol` -> `tolerance`. It just makes the code easier to read, IMO, and is self-documenting without someone having to guess what it is shor"

### R125: Method names must begin with an uppercase letter and use PascalCase.

- Scope: unspecified
- Support: 4 MRs, 4 threads, 2019-05-22 to 2023-08-07
- Reviewers: mwestphal (1), jpouderoux (1), francois.mazen (1), julien.fausty (1)
- [!10233](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10233) julien.fausty, 2023-08-07: "Also, please capitalize method names."
- [!7897](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7897) francois.mazen, 2021-04-27: "I foster method name that begin with a verb, so I would suggest a name like `SynchronizeDataArraySelectionRecursively`"
- [!5588](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5588) jpouderoux, 2019-08-19: "return => Return"

### R128: Rename functions to match their actual behavior, invocations, and naming style, including correcting typos and increasing verbosity where needed.

- Scope: unspecified
- Support: 4 MRs, 4 threads, 2020-03-06 to 2024-05-14
- Reviewers: michael.migliore (1), cory.quammen (1), dcthomp (1), spiros.tsalikis (1)
- [!10852](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10852) spiros.tsalikis, 2024-05-14: "This function name would probably be better if it was EnqueParticleToAnotherProcess, since it does not actually do any Controller Call."
- [!10538](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10538) dcthomp, 2023-09-25: "You renamed the function to `TestDegenerateCell()` but didn't rename the invocation."
- [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) michael.migliore, 2020-03-06: "I would rename this function to `RGBEReaderUpdateSlice`, what do you think? Yes more verbose !"

### R134: Use the `vtk` namespace for all symbols, including types and free functions, to avoid naming conflicts.

Rationale: Namespace symbol collision avoidance

- Scope: C++ code (types, free functions, and global namespace access)
- Support: 4 MRs, 4 threads, 2022-06-08 to 2026-07-03
- Reviewers: sankhesh (2), cory.quammen (1), timothee.chabat (1)
- [!13312](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13312) sankhesh, 2026-07-03: "It's the namespace convention in VTK, I prefer to follow it"
- [!12178](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12178) sankhesh, 2025-06-05: "1. Every free function should be in the "vtk" namespace. Rationale: Namespace symbol collision avoidance"
- [!9691](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9691) timothee.chabat, 2022-11-22: "I would use `namespace vtkCompositeArray` here (if possible ?), as we want to limit the number of symbols the user has access to IMO"

### R141: Rename variables to match existing naming patterns and local coding style to ensure consistency and reduce name conflicts.

Rationale: to reduce the chance of name conflicts in the future and for consistency with existing variable names

- Scope: C++ source code (implied by variable naming conventions like `MAX_STACK_ARRAY_SIZE`, `in_volumetricScatteringBlending`, `fieldDataValues`, `dataSetValues`)
- Support: 3 MRs, 3 threads, 2017-01-12 to 2022-07-14
- Reviewers: brad.king (1), timothee.chabat (1), jcfr (1)
- [!9381](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9381) jcfr, 2022-07-14: "For consistency with the variable name, I suggest `MAX_STACK_ARRAY_SIZE` -> `MAX_SCRATCH_ARRAY_SIZE` I concur, it will also reduce the chance of name conflicts in the future, as it is a little more sp"
- [!9231](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9231) timothee.chabat, 2022-06-01: "please rename `in_volumetricScatteringBlending` for case consistency (if it is already consistent)"
- [!2199](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2199) brad.king, 2017-01-12: "Please rename the variables to `fieldDataValues` and `dataSetValues` to be more consistent with local variable coding style used elsewhere."

### R176: Avoid naming variables the same as member variables to prevent confusion.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2018-05-31 to 2020-03-25
- Reviewers: LucasGandelKitware (1), jpouderoux (1), dcthomp (1)
- [!6620](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6620) dcthomp, 2020-03-25: "Can we name this something other than `fn` so that it is harder to confuse with `Shim.fn`?"
- [!6256](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6256) jpouderoux, 2019-12-04: "We should rename `CSVReader` to `InternalReader` for instance"
- [!4326](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4326) LucasGandelKitware, 2018-05-31: "Please use explicit names for member variable : `this->RenderWindow`"

### R177: Rename classes to better reflect their purpose or contents.

- Scope: C++ source classes
- Support: 3 MRs, 4 threads, 2018-09-27 to 2026-09-01
- Reviewers: mwestphal (2), ken-martin (1), utkarsh.ayachit (1)
- [!13550](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13550) mwestphal, 2026-09-01: "Not a great name lets find something more descriptive"
- [!9069](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9069) utkarsh.ayachit, 2022-04-21: "Can we rename this class to something like `vtkCompositeDataPipelineCache` or something? I think for now documenting it so that it's intended for use only in vtkCompositeDataPipeline internally may ma"
- [!4621](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4621) ken-martin, 2018-09-27: "Could you please rename the class to vtkCustomUniforms as it holds multiple uniforms."

### R179: Use 'Internal' or 'Internals' as a suffix for private classes; 'Impl' is acceptable but more specific.

Rationale: My preference is "Internal" or "Internals" as a suffix. Easy to say, not ambiguous, and plenty of precedent. "Impl" isn't bad either, but its meaning is a bit more specific, not all private classes are implementations of public interfaces.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2018-09-26 to 2024-07-29
- Reviewers: jpouderoux (1), cory.quammen (1), dgobbi (1)
- [!11352](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11352) dgobbi, 2024-07-29: "My preference is "Internal" or "Internals" as a suffix. Easy to say, not ambiguous, and plenty of precedent. "Impl" isn't bad either, but its meaning is a bit more specific, not all private classes ar"
- [!5773](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5773) cory.quammen, 2019-07-25: "How about changing this to `vtk3DLinearGridInternal`. There is precedent in VTK for using the `Internal` suffix to signify a class is private."
- [!4707](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4707) jpouderoux, 2018-09-26: "Internal => Internals"

### R182: Names of classes and methods should be pluralized (ending in 's') to match the actual data type, existing method names, or the corresponding file name.

- Scope: C++ class and method names
- Support: 3 MRs, 4 threads, 2019-04-16 to 2026-06-19
- Reviewers: jpouderoux (3), dcthomp (1)
- [!13356](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13356) dcthomp, 2026-06-19: "The question I have is w/r to the class's API - I had copied the ReadWire related method names from the original reader to minimize API changes but I think the proper name should be ReadWires - what d"
- [!5715](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5715) jpouderoux, 2019-07-03: "Should be "InitializeGraphic**s**Resources" (to match existing methods like "ReleaseGraphicsResources")"
- [!5354](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5354) jpouderoux, 2019-04-16: "`vtkOpenGLUniform` => `vtkOpenGLUniforms`"

### R189: Test files should be named in PascalCase, listed in alphabetical order, and named based on the class being tested.

- Scope: tests
- Support: 3 MRs, 3 threads, 2019-12-17 to 2026-08-11
- Reviewers: jpouderoux (1), acbauer (1), lucas.givord (1)
- [!13004](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13004) lucas.givord, 2026-08-11: "should be in PascalCase ? (same for other tests)"
- [!9092](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9092) acbauer, 2022-04-25: "You could put this in alphabetical order. Not a big deal though."
- [!6307](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6307) jpouderoux, 2019-12-17: "Should be called TestLinearCellExtrusion"

### R198: Avoid leading underscores in variable names and use trailing underscores for member variables to prevent conflicts with reserved identifiers and potential method names.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2021-02-09 to 2022-01-02
- Reviewers: olesen (1), dgobbi (1), ben.boeckel (1)
- [!8769](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8769) ben.boeckel, 2022-01-02: "I guess this should get renamed too? Indeed."
- [!8763](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8763) dgobbi, 2021-12-22: "Even though it isn't capitalized, should `_a_` be changed as well for consistency?"
- [!7600](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7600) olesen, 2021-02-09: "Couldn't we call these `data_` and `size_` etc? Otherwise can get ugly with data() and size() methods in the future."

### R208: Rename variables and methods to be more descriptive.

- Scope: unspecified
- Support: 3 MRs, 3 threads, 2023-01-17 to 2025-04-11
- Reviewers: mwestphal (2), lucas.givord (1)
- [!11986](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11986) mwestphal, 2025-04-11: "please rename `R`"
- [!11271](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11271) lucas.givord, 2024-07-05: "rename it CreateHierarchicalZBuffer()"
- [!9792](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9792) mwestphal, 2023-01-17: "please rename x"

## compiler-warnings

### R022: If a class has a virtual destructor (i.e., overrides a base class destructor or is intended for inheritance), its destructor must be marked with 'override' and, if no custom implementation is needed, should be defined as '= default'; if a class has virtual methods or overrides, it should have a virtual destructor.

- Scope: C++ source files
- Support: 12 MRs, 13 threads, 2018-01-10 to 2024-05-29
- Reviewers: ken-martin (6), charles.gueunet (5), sankhesh (1), thomas.galland (1)
- [!11165](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11165) thomas.galland, 2024-05-29: "here and in other classes: if not overridden, still add `~vtkWebGPUComputePipeline() override = default;`"
- [!11128](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11128) charles.gueunet, 2024-05-16: "virtual destructor instead, as it is intended for inheritance :grinning:"
- [!9193](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9193) charles.gueunet, 2022-05-17: "destructor should be virtual"

### R031: Mark intentionally unused parameters with the `vtkNotUsed` macro (or `vtkNoUsed` for arrays) instead of removing them or leaving them unnamed.

*Mixed evidence: check the examples before accepting.*

Rationale: Because `vtkNotUsed` has different semantics than `[[maybe_unused]]`—it explicitly indicates the parameter is intentionally not used, avoids compiler warnings, and preserves API compatibility for public/protected methods.

- Scope: C++ source code (function/method parameters)
- Support: 10 MRs, 10 threads, 2015-08-27 to 2026-07-09
- Reviewers: mwestphal (4), cory.quammen (1), drpeterfranz (1), ben.boeckel (1), charly.bollinger (1)
- [!13389](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13389) mathurin.lemarie, 2026-07-09: "its different. it doesnt mean the same thing for the dev reading the code. `[[maybe_unused]]` should be used when it may be unused, vtkNotUsed when it is not used. In that specific case, its a `vtkNot"
- [!10758](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10758) mwestphal, 2023-12-13: "use vtkNotUsed to avoid unused warnings"
- [!10587](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10587) charly.bollinger, 2023-10-11: "remove comment and replace with `vtkNotUsed(loc_id)`"
- Counter-evidence:
  - [!551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/551) dgobbi, 2015-08-19: "Some compilers on the dashboard complained about unused parameters "request" and "inputVector", so the names of those parameters should be omitted to silence the warnings:"

### R039: Remove unused variables to suppress compiler warnings.

- Scope: C++ sources
- Support: 9 MRs, 9 threads, 2017-01-17 to 2023-11-10
- Reviewers: mwestphal (6), dgobbi (2), demarle (1)
- [!10695](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10695) dgobbi, 2023-11-10: "warning: unused variable 'HASH_ERROR' [-Wunused-const-variable] warning: unused variable 'HASH_LINE' [-Wunused-const-variable] warning: unused variable 'HASH_PRAGMA' [-Wunused-const-variable]"
- [!9125](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9125) mwestphal, 2023-06-21: "you have a warning to fix: Core/vtkRenderer.cxx:1513:16: warning: unused variable 'closestProp' [-Wunused-variable]"
- [!9398](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9398) mwestphal, 2022-08-07: "Interaction/Widgets/vtkCompassWidget.cxx:124:29: warning: unused variable 'representation' [-Wunused-variable]"

### R050: Use VTK_FUTURE_CONST (or VTK_USE_FUTURE_CONST with #if) only when a method cannot be made const due to non-const internal usage, and avoid const VTK objects as parameters since VTK is not const-correct yet.

Rationale: VTK_FUTURE_CONST is needed to avoid false positives in CI when future const correctness is enabled, and const VTK objects are avoided to prevent const_cast usage since VTK objects are not const-safe yet.

- Scope: C++ source code
- Support: 7 MRs, 7 threads, 2016-04-25 to 2026-04-13
- Reviewers: seanm (2), alliepiper16 (1), yohann.bearzi (1), ben.boeckel (1), louis.gombert (1)
- [!13073](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13073) seanm, 2026-04-13: "I have said that again in the past, if we want to support future const, it should be enabled in our CI, otherwise things like that happen."
- [!12230](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12230) spiros.tsalikis, 2025-07-23: "all VTK_FUTURE_CONST can be replaced with const, given that this is a new class"
- [!12229](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12229) louis.gombert, 2025-07-09: "yes, unconsting is not-retrocompatible, consting is retro-compatible. `VTK_FUTURE_CONST` is only needed when a method cannot be set `const` because of method used internally which are not const yet."

### R064: Avoid direct comparison of integer expressions with different signedness by using static_cast or equivalent.

Rationale: Such comparisons produce compiler warnings (e.g., -Wsign-compare, C4018) that must be fixed to keep the dashboard clean.

- Scope: C++ sources
- Support: 6 MRs, 6 threads, 2018-11-01 to 2025-03-31
- Reviewers: mwestphal (2), cory.quammen (1), ken-martin (1), sebastien.jourdain (1), yohann.bearzi (1)
- [!12033](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12033) mwestphal, 2025-03-31: "warning: comparison of integer expressions of different signedness: 'int' and 'std::vector<vtkGLTFDocumentLoader::Accessor>::size_type' {aka 'long unsigned int'} [-Wsign-compare]"
- [!7701](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7701) mwestphal, 2021-03-01: "the compiler cannot know if `node.Camera` is unsigned so it raises a sign mismatch warning here."
- [!7260](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7260) yohann.bearzi, 2020-09-28: "You have to `static_cast` one way or another so you don't compare signed integer with unsigned integer."

### R094: Fix all compiler warnings introduced by the change prior to merging.

- Scope: unspecified
- Support: 5 MRs, 5 threads, 2018-03-22 to 2023-02-21
- Reviewers: ken-martin (3), demarle (1), vbolea (1)
- [!9869](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9869) vbolea, 2023-02-21: "On another topic we need to address the newly introduced compiler warnings before approval."
- [!8411](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8411) ken-martin, 2021-09-16: "At least one compiler warning introduced I believe. Take a look through the output and try pushing a fix for any you see. Thanks!"
- [!5490](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5490) ken-martin, 2019-05-06: "Please fix warnings prior to merging."

### R106: Avoid implicit conversions between `size_t` and `int`; use `static_cast` when necessary to prevent C4267 warnings about possible data loss.

*Mixed evidence: check the examples before accepting.*

Rationale: To prevent compiler warning C4267: 'conversion from size_t to int, possible loss of data'.

- Scope: C++ code where `size_t` and `int` types interact (e.g., array indexing, size calculations, function arguments).
- Support: 4 MRs, 4 threads, 2022-02-10 to 2026-07-06
- Reviewers: mwestphal (2), todoooo (1), finetjul (1)
- [!13359](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13359) finetjul, 2026-07-06: "Warning C4267: 'argument': conversion from 'size_t' to 'int', possible loss of data"
- [!13080](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13080) mwestphal, 2026-04-01: "warning C4267: '=': conversion from 'size_t' to 'int', possible loss of data"
- [!12909](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12909) mwestphal, 2026-02-09: "-0+0 new unsigned char[static_cast<size_t>(ysize) * static_cast<size_t>(xsize) * static_cast<size_t>(bytesPerPixel)];"
- Counter-evidence:
  - [!3941](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3941) jpouderoux, 2018-04-28: "And replace int by size_t"
  - [!5930](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5930) mwestphal, 2021-04-30: "About "..\VTK\Common\Core\vtkFFT.cxx(26): warning C4267: 'argument': conversion from 'size_t' to 'int', possible loss of data" and "..\VTK\Common\Core\vtkFFT.cxx(44): warning C4267: 'argument': conver"

### R122: Use std::move when transferring ownership of non-temporary objects, but avoid std::move on temporary objects to prevent copy elision warnings and redundant moves.

Rationale: std::move avoids unnecessary copies when transferring ownership of containers (Charles Gueunet), is redundant for temporaries (Mathieu Westphal), prevents slow copy constructors for std::vector members during removal (Cory Quammen), and avoids warnings about preventing copy elision when applied to temporaries (Mathieu Westphal).

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2018-01-08 to 2023-08-24
- Reviewers: mwestphal (2), cory.quammen (1), charles.gueunet (1)
- [!10355](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10355) charles.gueunet, 2023-08-24: "would it make sense to `std::move(buff)` here ? (and in the other `Set` too) very much so"
- [!9284](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9284) mwestphal, 2022-06-16: "spiros.tsalikis: "Well, I think that the std::move here is redundant, because the object is temporary, so the warning is correct.""
- [!9014](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9014) cory.quammen, 2022-04-04: "If you don't do that, you're calling the copy constructor and that's slow for this kind of objects."

### R137: Avoid implicit conversion from bool or double to bool; use !! to make boolean conversion explicit.

Rationale: Some compilers do not like implicit boolean conversion.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2022-12-29 to 2026-03-04
- Reviewers: timothee.chabat (2), spiros.tsalikis (1), ahernsean (1)
- [!12983](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12983) ahernsean, 2026-03-04: "avoiding implicit bool -> int conversion I guess"
- [!12321](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12321) spiros.tsalikis, 2025-12-09: "Some compilers do not like implicit boolean conversion. `!!` makes the conversion explicit."
- [!9868](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9868) timothee.chabat, 2023-01-30: "avoid implicit conversion from double to bool"

### R170: Fix warnings before merging.

Rationale: to avoid nightly dashboard issues

- Scope: unspecified
- Support: 3 MRs, 3 threads, 2017-07-10 to 2020-10-29
- Reviewers: dgobbi (1), utkarsh.ayachit (1), LucasGandelKitware (1)
- [!7364](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7364) LucasGandelKitware, 2020-10-29: "Warnings have been fixed."
- [!6290](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6290) utkarsh.ayachit, 2020-02-13: "there are a few warnings. once you've fixed those, feel free to merge."
- [!3008](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3008) dgobbi, 2017-07-10: "But I recommend that the `double zaxis[3] = {0, 0, 1};` issue above be fixed before merge, because it's likely to cause warnings on some of the nightly dashboards."

### R185: Deprecate an existing function and add a new function with a similar name, while keeping a legacy version alongside it to avoid warnings.

Rationale: To help developers transition to new functions and avoid warnings.

- Scope: C++ functions (specifically those with setters like SetUserPythonPath, and their legacy counterparts)
- Support: 3 MRs, 3 threads, 2019-09-18 to 2024-03-18
- Reviewers: mwestphal (1), julien.fausty (1), danlipsa (1)
- [!10969](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10969) danlipsa, 2024-03-18: "I would deprecate SetUserPythonPath and add a new function AddUserPythonPath that does the same."
- [!9812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9812) julien.fausty, 2023-04-17: "I kept the naming of the existing functions to help developper do the switch."
- [!5995](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5995) mwestphal, 2019-09-18: "this one makes sense, but you need to keep a legacy version alongside it."

## build-cmake

### R037: Commit messages must have a short first line (≤50–78 characters), followed by an empty line, then a more detailed description.

- Scope: unspecified
- Support: 9 MRs, 9 threads, 2016-03-22 to 2023-03-20
- Reviewers: cory.quammen (2), julien.fausty (2), utkarsh.ayachit (1), demarle (1), mwestphal (1)
- [!7521](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7521) mwestphal, 2023-03-20: "Yes, ammend your commit message."
- [!10059](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10059) julien.fausty, 2023-03-17: "There is no strict requirements regarding git commit messages syntax but try to be as informative as possible: git commit -m "Short yet informative commit message". A good rule of thumb for your short"
- [!10052](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10052) julien.fausty, 2023-03-13: "Please prefix your commit message with `HyperTreeGridAxisClip:` (or something similarly informative) so that it is explicit which area of VTK the fixes were applied to"

### R071: Target the merge request to the newest branch (e.g., master), and use Backport: trailers in the MR description to indicate additional release branches to backport to.

- Scope: unspecified
- Support: 6 MRs, 6 threads, 2019-01-24 to 2025-05-21
- Reviewers: seanm (2), ben.boeckel (1), cory.quammen (1), dgobbi (1), berkgeveci (1)
- [!12121](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12121) berkgeveci, 2025-05-21: "the backport trailer in the description tells the robot to do that"
- [!10199](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10199) seanm, 2023-05-12: "Yep, the MR targets the "newest" and we backport to "older" branches (release MRs are "special" and do it "backwards")."
- [!8846](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8846) seanm, 2022-01-31: "the MR 'main target' (what gitlab knows about) should be 'the newest branch' (here, `master`)"

### R088: Mark dependencies as PRIVATE_DEPENDS when they are not part of the public API or when the new header does not use the module.

Rationale: Marking a dependency as private avoids adding it to include/link lines where it isn't needed.

- Scope: CMake module definitions
- Support: 5 MRs, 5 threads, 2016-04-14 to 2023-01-03
- Reviewers: utkarsh.ayachit (2), mwestphal (2), ben.boeckel (1)
- [!9499](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9499) ben.boeckel, 2023-01-03: "Sorry, moved to `PRIVATE_DEPENDS`."
- [!6101](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6101) mwestphal, 2020-06-02: "Yes, the new header does not use the module."
- [!4045](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4045) mwestphal, 2018-04-03: "this could go into PRIVATE_DEPENDS"

### R092: Remove unused and useless includes and sort the remaining ones.

- Scope: tests
- Support: 5 MRs, 5 threads, 2017-11-23 to 2025-11-19
- Reviewers: jpouderoux (2), mwestphal (2), michael.migliore (1)
- [!12611](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12611) mwestphal, 2025-11-19: "please cleanup and organise includes"
- [!12056](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12056) mwestphal, 2025-04-14: "You can remove this include. Please cleanup all includes as needed :smile:"
- [!4019](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4019) jpouderoux, 2018-03-07: "Please remove all useless include files for those tests."

### R112: Optional dependencies must be declared as PRIVATE_DEPENDS and processed together with private modules, not as optional in function signatures.

*Mixed evidence: check the examples before accepting.*

- Scope: CMake module files
- Support: 4 MRs, 4 threads, 2021-11-19 to 2025-08-05
- Reviewers: ben.boeckel (3), ryan.krattiger1 (1)
- [!12251](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12251) ben.boeckel, 2025-08-05: "These should never be "optional", so this can be removed. Might be better to do this in an optional-specific loop to gather the "enabled" optional modules then process optional and private together si"
- [!10898](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10898) ben.boeckel, 2024-03-12: "Optional deps are always treated as private if they exist."
- [!9549](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9549) ben.boeckel, 2022-11-15: "This is wrong. `#ifdef` is not right because it is *always* defined. It is instead, a value or `0` or `1`. However, optional dependencies are always private, so code including `vtkGenericDataArray.h` "
- Counter-evidence:
  - [!13231](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13231) ben.boeckel, 2026-05-14: "This should be `ORDER_DEPENDS`. `OPTIONAL_DEPENDS` will end up being linked (privately) if it is around."

### R140: Use TEST_OPTIONAL_DEPENDS instead of TEST_DEPENDS for tests that depend on optional modules so that only tests with all dependencies available are added.

*Mixed evidence: check the examples before accepting.*

Rationale: TEST_DEPENDS means that if any module in the list is not available, no testing is done; instead, these should become TEST_OPTIONAL_DEPENDS and only the tests which have all dependencies available be added.

- Scope: tests
- Support: 3 MRs, 3 threads, 2019-10-24 to 2022-11-21
- Reviewers: ben.boeckel (2), charles.gueunet (1)
- [!9697](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9697) ben.boeckel, 2022-11-21: "Could you please look at using `TEST_OPTIONAL_DEPENDS`. Tests can be gated on `if (TARGET VTK::IOEnSight)` then."
- [!9230](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9230) charles.gueunet, 2022-05-31: "I think it would be better. Here, we would require `eigen` to test the DataModel module, which basically means that all VTK testing would require `eigen`. I would rather have the new test disabled whe"
- [!6103](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6103) ben.boeckel, 2019-10-24: "TEST_DEPENDS means that if any module in that list is not available, *no* testing is done. Instead, these should almost certainly become TEST_OPTIONAL_DEPENDS and only the tests which have all depende"
- Counter-evidence:
  - [!328](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/328) berkgeveci, 2015-06-28: "This should be a TEST_DEPENDS. We don't want to create a dependency to the IO modules from filters modules. It should be possible to compile filters without needing IO classes. Test dependency to IO m"

### R155: Do not include hard tabs; use 2-space indentation instead, and avoid whitespace changes except in separate commits.

Rationale: Hard tabs pollute history, make reviews take longer, break VTK's style guides, and are not allowed in the repository.

- Scope: VTK code repository (implied for all source files, as hard tabs and indentation style are general coding conventions)
- Support: 3 MRs, 3 threads, 2015-08-18 to 2018-03-22
- Reviewers: ben.boeckel (1), dgobbi (1), demarle (1)
- [!4099](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4099) demarle, 2018-03-22: "Try to avoid whitespace changes, they pollute the history, make it take longer to review, and usually break VTK's style guides."
- [!1263](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1263) dgobbi, 2016-02-24: "Hard tabs are not allowed in the VTK code repository, they must be converted to the correct number of spaces."
- [!495](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/495) ben.boeckel, 2015-08-18: "VTK also uses 2-space indentation. Please replace your tabs (kwrobot will not allow the branch otherwise)."

### R156: Tests that do not require a validation image must be listed with the NO_VALID keyword and placed in their own section alongside NO_DATA and NO_OUTPUT.

- Scope: tests
- Support: 3 MRs, 3 threads, 2015-12-30 to 2026-08-06
- Reviewers: dgobbi (1), cory.quammen (1), lucas.givord (1)
- [!13004](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13004) lucas.givord, 2026-08-06: "No baselines for these tests. See the `NO_VALID` keyword above."
- [!4755](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4755) cory.quammen, 2018-10-05: "Change line 21 to `TestDelaunay2DBestFittingPlane.cxx,NO_VALID`. That means there is no validation image to check against when the test is finished."
- [!1043](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1043) dgobbi, 2015-12-30: "This test does not use a regression image, so it shouldn't be listed with the other tests. It should be in its own section with `NO_DATA` (needs no input data) `NO_VALID` (needs no regression image) a"

### R157: Set system include directories before calling `vtk_module_library` and use `vtk_module_include` for include directories in module definitions without re-ordering `${vtk-module}_INCLUDE_DIRS`.

Rationale: Because `${vtk-module}_INCLUDE_DIRS` is exposed publicly and not all consumers will use BEFORE, and system include directories must be set before `vtk_module_library` to ensure correct ordering.

- Scope: CMake module files
- Support: 3 MRs, 3 threads, 2016-03-28 to 2024-08-20
- Reviewers: demarle (1), brad.king (1), ben.boeckel (1)
- [!1763](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1763) brad.king, 2016-08-04: "We should avoid re-ordering ${vtk-module}_INCLUDE_DIRS because that value is exposed publicly (and internally to other modules). Not all consumers will use BEFORE."
- [!1235](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1235) demarle, 2016-03-28: "set(${vtk-module}_SYSTEM_INCLUDE_DIRS ${OPENSLIDE_INCLUDE_DIRS}) To Domains/Microscopy/CMakeLists.txt just before vtk_module_library."
- [!11415](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11415) ben.boeckel, 2024-08-20: "Please use `vtk_module_include`"

### R160: Do not use variable-length stack arrays or new custom stack-based vector classes; use std::vector or stack-allocated raw arrays instead.

Rationale: Variable-length stack arrays are not supported by MSVC, and introducing new data structures like vtkStackVector incurs maintenance cost and compiler compatibility issues without sufficient performance benefit.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2017-01-13 to 2021-02-10
- Reviewers: alliepiper16 (1), michael.migliore (1), cory.quammen (1)
- [!7600](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7600) cory.quammen, 2021-02-10: "When weighing wether to introduce a new data structure like vtkStackVector, it's important to consider the cost of maintenance of the new class with the performance improvement it offers. In most case"
- [!6240](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6240) michael.migliore, 2019-12-12: "Why the points are allocated on the heap? It looks that this cannot be nullptr, so stack variables looks better to me."
- [!2335](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2335) alliepiper16, 2017-01-13: "This is the problem -- MSVC doesn't support C99 in it's C++ compiler, and variable sized stack arrays are one of the missing features. This is why the original implementation jumped through hoops to u"

### R168: A filter module must not depend on an IO module.

- Scope: CMake module dependencies (specifically between Filters and IO kits)
- Support: 3 MRs, 3 threads, 2017-06-09 to 2020-06-02
- Reviewers: berkgeveci (2), mwestphal (1)
- [!6101](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6101) mwestphal, 2020-06-02: "As for private, it won't fix the problem. `FiltersFlowPaths` is not allowed here (private or public: it depends on `IOCore` which is not allowed from the `Filters` kit)."
- [!6784](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6784) berkgeveci, 2020-04-24: "We have avoided IO type dependencies in these classes so far. Can't this be pushed down to some IO thing?"
- [!2926](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2926) berkgeveci, 2017-06-09: "A filter module should not depend on an IO module. Is this for the testing by any chance? Then it should be a test dependency"

### R175: Call Modified() only when the method has an effect, and only after verifying the value actually changed.

Rationale: Without Modified(), there is zero reason to check != before setting; the standard pattern is to only call Modified() if its value is actually changed.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2018-04-09 to 2022-08-16
- Reviewers: ben.boeckel (2), dcthomp (1)
- [!9101](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9101) ben.boeckel, 2022-08-16: "Without `Modified()`, there is zero reason to check `!=` before setting."
- [!7516](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7516) ben.boeckel, 2022-05-21: "This is always called. The standard pattern is to only call it if its value is actually changed."
- [!4170](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4170) dcthomp, 2018-04-09: "On a lot of these, it would be better to ensure that `this->Modified()` is only called when the method has an effect. For example, check the return value of `this->BlockPickabilities.erase(data_object"

### R181: Top-level cache variables in VTK module system code must not be named VTK_*; instead, options should be passed as arguments to vtk_module_build() or set using set(CACHE STRING) before vtkModule.cmake executes, and unconditionally set variables should have their definitions factored out into variables.

- Scope: VTK module system CMake code
- Support: 3 MRs, 3 threads, 2019-02-05 to 2023-05-25
- Reviewers: ben.boeckel (1), svenevs (1), mwestphal (1)
- [!10200](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10200) mwestphal, 2023-05-25: "ben.boeckel: "No. `vtkModule` should *never* have a cache variable at the top-level (certainly not named `VTK_*`). This should be an argument to `vtk_module_build()` that VTK passes in the value of so"
- [!9541](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9541) svenevs, 2022-09-19: "they should be set(CACHE STRING not INTERNAL"
- [!5132](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5132) ben.boeckel, 2019-02-05: "When a variable is unconditionally set, I've been factoring out the `vtk_module_definitions` and using a variable for the value. Just a nit though."

### R204: All VTK options should start with `VTK_`.

- Scope: unspecified
- Support: 3 MRs, 3 threads, 2022-01-26 to 2026-01-27
- Reviewers: ben.boeckel (2), jaswant.panchumarti (1)
- [!12665](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12665) jaswant.panchumarti, 2026-01-27: "This should be VTK_FACTORY_PREFER"
- [!9101](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9101) ben.boeckel, 2022-06-16: "All VTK options should start with `VTK_`."
- [!8839](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8839) ben.boeckel, 2022-01-26: "all VTK options should start with `VTK_`"

## api-usage

### R048: Use SafeDownCast instead of static_cast, dynamic_cast, or reinterpret_cast for downcasting VTK objects.

*Mixed evidence: check the examples before accepting.*

- Scope: C++ sources
- Support: 7 MRs, 8 threads, 2020-08-19 to 2026-03-26
- Reviewers: charles.gueunet (2), utkarsh.ayachit (1), timothee.chabat (1), finetjul (1), tiffany.chhim (1)
- [!13052](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13052) mwestphal, 2026-03-23: "FastDownCast if you are sure its an vtkAppendPolyData, SafeDownCast (and check) if you are not."
- [!8303](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8303) finetjul, 2021-09-08: "Use safedowncast instead of reinterpret_cast"
- [!7774](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7774) timothee.chabat, 2021-03-23: "I wanted to make the code more readable by moving the "SafeDownCast" in the callee instead of polluting the read flow before the the call to MergeGhostArray."
- Counter-evidence:
  - [!1453](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1453) alliepiper16, 2016-04-25: "Performance -- `SafeDownCast` can be really expensive depending on how deep the inheritance hierarchy is. Might as well just use `static_cast` when not checking the return value."
  - [!5439](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5439) jpouderoux, 2019-04-18: "smartpointers are useless here"
  - [!8627](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8627) tiffany.chhim, 2021-11-10: "This gets called roughly once per actor per eye pre render. So it can get called a lot. SafeDownCast costs CPU time as it makes a virtual function call and then does a string comparison which will usu"

### R076: Use vtkArrayDispatch dispatchers (e.g., DispatchByArray, Dispatch2BySameValueType, Dispatch3BySameValueType, Dispatch) for array operations instead of std::vector or manual iteration.

Rationale: To avoid copies, reduce virtual function calls, enable compiler optimizations, and follow established patterns like vtkMergeVectorComponents.

- Scope: C++ array processing code that operates on VTK data arrays
- Support: 6 MRs, 7 threads, 2019-11-12 to 2026-04-03
- Reviewers: alliepiper16 (3), cory.quammen (2), spiros.tsalikis (2)
- [!13105](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13105) spiros.tsalikis, 2026-04-03: "if possible, i would suggest to replace std::vector\<double\> by getting the underlying arrays of the points and dispatching via that using vtkArrayDispatch::DispatchByArray<vtkArrayDispatch::PointArr"
- [!13017](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13017) spiros.tsalikis, 2026-03-12: "Highly recommend using Dispatching here so that you can use DataArrayValueRange and DataArrayTupleRange to avoid copies."
- [!8379](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8379) cory.quammen, 2021-09-03: "We should still use `vtkArrayDispatch` to access data arrays as fast as possible. You can either do this inside the `operator()` in the functor or do the array dispatch in `RequestData()`."

### R096: Add `const` to pointer parameters (e.g., `const T*`) when the parameter is not modified.

Rationale: The reviewers indicated that constness should be used when parameters are not modified, and that adding `const` to pointer parameters is acceptable and should be almost completely backwards compatible.

- Scope: C++ source code (specifically function parameters in headers and implementations)
- Support: 5 MRs, 5 threads, 2018-06-25 to 2024-06-25
- Reviewers: dgobbi (2), utkarsh.ayachit (1), ben.boeckel (1), jaswant.panchumarti (1)
- [!11261](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11261) jaswant.panchumarti, 2024-06-25: "ditto, can this be `const`?"
- [!10510](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10510) dgobbi, 2023-09-15: "Add `const FunctionInfo* theFunc` (ditto for header file)."
- [!9499](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9499) ben.boeckel, 2023-01-03: "Can it be `const*` then? Sure. Done."

### R105: Virtual methods must be declared virtual in base classes if derived classes override them to add functionality.

*Mixed evidence: check the examples before accepting.*

Rationale: The base class method must be virtual so that derived class overrides are properly invoked, especially when the base class (e.g., vtkObjectBase) calls the method (e.g., in PrintHeader) and expects derived behavior (e.g., including ObjectName).

- Scope: C++ header files where virtual methods are declared in base classes that are overridden in derived classes to add functionality.
- Support: 4 MRs, 5 threads, 2018-01-16 to 2024-11-12
- Reviewers: mwestphal (3), ben.boeckel (2)
- [!10356](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10356) ben.boeckel, 2023-08-17: "At a minimum, vtkStringArray, vtkFloatArray, vtkDoubleArray."
- [!8897](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8897) ben.boeckel, 2022-02-14: "Yes it has to be virtual: vktObjectBase doesn't know about the ObjectName and just returns the class name and pointer like before. the vtkObject override adds the ObjectName if it is set. vtkObjectBas"
- [!3767](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3767) mwestphal, 2018-01-16: "This method is implemented in vtkOpenGLGlyph3DMapper, current implementation always returns zero. ` `This method is intended to be reimplemented in inherited classes, this class implementation does no"
- Counter-evidence:
  - [!5588](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5588) michael.migliore, 2019-06-27: "remove virtual"

### R111: Use vtkArrayDownCast for array downcasting instead of SafeDownCast, and assign the result to a variable before checking for null.

Rationale: vtkArrayDownCast is more efficient for data arrays and performs the safe downcast automatically when using pointData->GetArray(idx).

- Scope: C++ sources handling VTK arrays
- Support: 4 MRs, 4 threads, 2021-10-27 to 2026-03-18
- Reviewers: yohann.bearzi (1), charles.gueunet (1), charly.bollinger (1), mwestphal (1)
- [!12852](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12852) mwestphal, 2026-03-18: "if (vtkUnsignedCharArray* colorArray = vtkArrayDownCast<vtkUnsignedCharArray>(input->GetPointData()->GetArray(this->ColorArrayName.data())))"
- [!9346](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9346) charles.gueunet, 2022-07-12: "for data array, you may privilege the more efficient vtkArrayDownCast"
- [!8567](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8567) yohann.bearzi, 2021-10-27: "For arrays, `vtkArrayDownCast<ArrayType>` is a better alternative to the `SafeDownCast`."

### R139: Prefer using vtk::DataArrayValueRange over GetVoidPointer or GetPointer interfaces.

- Scope: C++ sources
- Support: 3 MRs, 5 threads, 2022-12-02 to 2026-09-18
- Reviewers: julien.fausty (3), mwestphal (1), spiros.tsalikis (1)
- [!13593](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13593) spiros.tsalikis, 2026-09-18: "Other than squashing the 3 fixup commits that i see, the only last thing i would suggest is. Keep the GetDeviceVoidPointer in vtkDataArray as it was, but implement it using GetDevicePointer. GetDevice"
- [!12403](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12403) mwestphal, 2025-10-23: "b56a6b54c7 vtkAbstractArray: Replace GetVoidPointer with GetVariantValue"
- [!9710](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9710) julien.fausty, 2022-12-02: "Avoid using the `GetVoidPointer` prefer using the ranges provided by `vtk::DataArrayValueRange` for example for easy iterators."

### R144: Call Set methods in the constructor for properties that are never changed afterwards.

- Scope: C++ source code
- Support: 3 MRs, 3 threads, 2018-03-02 to 2023-08-17
- Reviewers: utkarsh.ayachit (1), mwestphal (1), ben.boeckel (1)
- [!10356](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10356) ben.boeckel, 2023-08-17: "Because most Set methods in VTK are virtual (see `vtkSetMacro()`)?"
- [!6101](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6101) mwestphal, 2019-12-12: "I mean to call : `this->vtkRuledSurface->SetRuledModeToResample();` in your constructor since it is never changed."
- [!3986](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3986) utkarsh.ayachit, 2018-03-02: "a bit non-VTK-pattern, but I defer to you. We don't generally have set methods that return values."

### R146: Use reference for output parameters when null is not expected; use pointer when the output may be null or when the output is initialized to (0,0) and passed by value.

*Mixed evidence: check the examples before accepting.*

- Scope: C++ function parameters
- Support: 3 MRs, 3 threads, 2021-02-18 to 2024-06-06
- Reviewers: LucasGandelKitware (1), lassoan (1), lucas.givord (1)
- [!11199](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11199) lucas.givord, 2024-06-06: "to fit with the previous code, we should pass fileID in reference"
- [!7790](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7790) lassoan, 2021-03-26: "Do you expect to get numberOfNodes==nullptr? If not then use int &numberOfNodes."
- [!7624](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7624) LucasGandelKitware, 2021-02-18: "This is sent by copy, out is (0,0) when returning from the fonction. Use pointers instead."
- Counter-evidence:
  - [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) jpouderoux, 2020-03-09: "looks like you could directly use outPtr instead as it is not given as a reference"

### R169: Use vtkDataObject::GetNumberOfElements(attributeType) instead of manual iteration, downcasting, or explicit if/else blocks to determine tuple or element counts.

Rationale: Because GetNumberOfElements is the new API that directly provides the count without requiring manual iteration or type-specific branching.

- Scope: C++ sources using VTK arrays and composite data sets
- Support: 3 MRs, 3 threads, 2017-06-26 to 2025-08-12
- Reviewers: utkarsh.ayachit (2), dgobbi (1)
- [!11986](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11986) dgobbi, 2025-08-12: "Shouldn't this use `GetNumberOfTuples()`? For VTK arrays, `GetSize()` means something different."
- [!5446](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5446) utkarsh.ayachit, 2019-04-23: "minor suggestion for cleanup here. `vtkDataObject::GetNumberOfElements` is new API. I'd recommend changing this override implementation to iterate over the blocks using iterator and then call `iter->G"
- [!2965](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2965) utkarsh.ayachit, 2017-06-26: "Then simply call vtkDataObject::GetNumberOfElements(attributeType). No need for the explicit if/else."

## python-wrapping

### R090: Use `vtkSmartPointer::Take()` or `vtkSmartPointer::TakeReference()` to transfer ownership of a VTK object to an existing smart pointer, avoiding unnecessary copying or raw pointer assignment.

- Scope: C++ sources
- Support: 5 MRs, 5 threads, 2017-01-10 to 2025-01-28
- Reviewers: dgobbi (1), mwestphal (1), julien.fausty (1), leon.victor (1), cory.quammen (1)
- [!11750](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11750) cory.quammen, 2025-01-28: "This was using the old style before it got replaced with `vtk::TakeSmartPointer`. Just didn't do that consistently."
- [!11361](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11361) leon.victor, 2024-08-13: "Use `vtkSmartPointer::Take` or `vtkSmartPointer::TakeReference` to avoid copying to an already existing smart ptr"
- [!10443](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10443) julien.fausty, 2023-08-28: "error: use of deleted function ‘void vtkSmartPointer<ArrayType>::TakeReference(const vtkSmartPointerBase&) [with T = vtkDataArray]’ 653 | array.TakeReference(vtkSmartPointer<vtkDoubleArray>::New()); a"

### R109: Remove unused or unreferenced formal parameters from function signatures.

- Scope: function signatures in C++ code
- Support: 4 MRs, 4 threads, 2020-11-05 to 2026-07-02
- Reviewers: cory.quammen (1), ken-martin (1), thomas.galland (1), finetjul (1)
- [!13359](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13359) finetjul, 2026-07-02: "v is not used, is it ?"
- [!10032](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10032) thomas.galland, 2023-03-08: "correct but as we discuss we don't really need this parameter, I removed it"
- [!8608](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8608) ken-martin, 2021-11-08: "This has added compiler warnings to master's build"

### R172: Use `from vtkmodules import ...` or `from vtkmodules.vtk<KitName> import ...` for imports

Rationale: to avoid having some other module failing to load cause the import to fail as well and to avoid importing all of VTK

- Scope: Python wrapping
- Support: 3 MRs, 3 threads, 2017-12-15 to 2020-01-22
- Reviewers: ben.boeckel (2), jcfr (1)
- [!6402](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6402) ben.boeckel, 2020-01-22: "It's better to `from vtkmodules import vtkIOADIS` to avoid having some other module failing to load causing this to fail as well."
- [!6304](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6304) ben.boeckel, 2019-12-23: "Please use `from vtkmodules.vtkIODICOM import …` to avoid importing all of VTK."
- [!3674](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3674) jcfr, 2017-12-15: "With the use of `vtkmodules`, it look like it is still required to explicitly import a kit and its dependencies."

### R184: Use SetValue instead of SetTuple1 for known-type arrays in C++ code to avoid overhead, and reserve SetTuple*/GetTuple* APIs for Python wrapping.

Rationale: Using SetValue has less overhead when working with known-type vtkXXXArray, and SetTuple*/GetTuple* APIs should be reserved for Python code.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2021-04-13 to 2026-02-05
- Reviewers: timothee.chabat (1), yohann.bearzi (1), olesen (1)
- [!12885](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12885) olesen, 2026-02-05: "I thought that SetTuple1 etc are only for wrappers."
- [!9243](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9243) yohann.bearzi, 2022-06-06: "I believe that we're trying to move away from the `SetTuple*` / `GetTuple*` API and reserve it for python code."
- [!5930](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5930) timothee.chabat, 2021-04-13: "Using `->SetValue(...)` has less overhead when working with known-type `vtkXXXArray`"

### R195: Use vtk_module_test_data() in CMake for test data directories and vtkTestUtilities::ExpandDataFileName in C++ tests for test data file paths.

- Scope: tests
- Support: 3 MRs, 3 threads, 2020-07-13 to 2023-09-01
- Reviewers: utkarsh.ayachit (1), aangelos28 (1), julien.fausty (1)
- [!7181](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7181) aangelos28, 2020-09-07: "See the `vtk_module_test_data` calls in the tree."
- [!7101](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7101) utkarsh.ayachit, 2020-07-13: "don't parse arguments like so. Instead use `vtkTestUtilities::ExpandDataFileName`. See `TestIossExodus.cxx` for a example."
- [!10459](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10459) julien.fausty, 2023-09-01: suggested `if (NOT vtk_testing_cxx_disabled) vtk_module_test_data() add_subdirectory(Cxx) endif ()`

### R200: Do not use `vtkStdString`; use `std::string` instead.

Rationale: Returning const std::string& would force the implementation to store an std::string internally forever, and `std::string` is always better.

- Scope: all C++ sources
- Support: 3 MRs, 3 threads, 2021-05-12 to 2022-08-29
- Reviewers: ben.boeckel (2), lassoan (1)
- [!9398](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9398) ben.boeckel, 2022-08-29: "Please do not add new instances of `vtkStdString`. `std::string` is always better."
- [!8897](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8897) lassoan, 2022-02-14: "Returning const std::string& would force the implementation of this class to store an std::string internally forever. Therefore, in libraries that offer stable API in the long term the best practice i"
- [!7907](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7907) ben.boeckel, 2021-05-12: "Please just use `std::string`. New uses of `vtkStdString` should be avoided."

## docs-release-notes

### R069: Use doxygen-style comments (including proper doxygen blocks, doc blocks, and block comments) for documentation.

- Scope: unspecified
- Support: 6 MRs, 6 threads, 2018-05-24 to 2025-11-10
- Reviewers: mwestphal (2), charles.gueunet (2), jpouderoux (1), michael.migliore (1)
- [!12602](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12602) mwestphal, 2025-11-10: "use a proper doxygen block"
- [!10609](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10609) charles.gueunet, 2023-10-23: "doxygen block comment (here and below)"
- [!6567](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6567) michael.migliore, 2020-03-24: "use doxygen style comments"

### R072: Do not use a doxygen group when there is a single method.

- Scope: C++ sources
- Support: 6 MRs, 6 threads, 2019-04-16 to 2025-12-10
- Reviewers: mwestphal (4), jpouderoux (1), lucas.givord (1)
- [!12664](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12664) mwestphal, 2025-12-10: "When there is a single method, it is not needed."
- [!9763](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9763) lucas.givord, 2023-03-10: "missing ` ///@}` here to avoid bad doxygen generation"
- [!9602](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9602) mwestphal, 2022-11-23: "doxygen group not needed"

### R101: Add a changelog entry in `Documentation/release/dev` for new features or changes.

- Scope: unspecified
- Support: 5 MRs, 5 threads, 2022-01-19 to 2026-07-09
- Reviewers: mwestphal (3), sankhesh (1), spiros.tsalikis (1)
- [!13438](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13438) mwestphal, 2026-07-09: "Please add a release note in `Documentation/release/dev`"
- [!12764](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12764) spiros.tsalikis, 2026-01-29: "could you also add a changelog, so when people read the release notes, they can see all the cool things you added?"
- [!12335](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12335) sankhesh, 2025-08-01: "Yes, please add a new changelog under `Documentation/release/dev`. It will be ported to release notes at tagging time."

### R193: Add standard SPDX license headers to all new files.

- Scope: new files
- Support: 3 MRs, 3 threads, 2020-05-27 to 2025-09-16
- Reviewers: ben.boeckel (1), mwestphal (1), timothee.couble (1)
- [!12459](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12459) timothee.couble, 2025-09-16: "// SPDX-FileCopyrightText: Copyright (c) Kitware Inc. // SPDX-FileCopyrightText: Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen // SPDX-License-Identifier: BSD-3-Clause"
- [!9369](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9369) mwestphal, 2022-07-08: "Add standard license headers to all files"
- [!6917](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6917) ben.boeckel, 2020-05-27: "Copyright header"

## threading-smp

### R097: Use vtkSMPTools::For for parallel loops over mesh cells, and consider vtkSMPTools::For or vtkSMPTools::Sort for loops and sorts when not already in a threaded function.

- Scope: C++ sources
- Support: 5 MRs, 6 threads, 2019-05-31 to 2026-05-26
- Reviewers: timothee.chabat (3), will.schroeder (2), spiros.tsalikis (1)
- [!13105](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/13105) spiros.tsalikis, 2026-05-26: "This could use vtkSMPTools to do the assigning, i think."
- [!9821](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9821) timothee.chabat, 2023-01-06: "There is a few loops / sorts that could be SMP-fied (vtkSMPTools::For, vtkSMPTools::Sort), except if we already are in a threaded function"
- [!8182](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8182) will.schroeder, 2021-08-05: "As you can see from the code, I already use vtkSMPTools for threading. Multithreading was one of the basic requirements that @cory.quammen gave me while I was researching for the best possible mathema"

### R188: Use `vtkSMPThreadLocal` or `vtkSMPThreadLocalObject` to create one instance per thread when using `vtkLabelMapLookup` in an SMP parallel context, and prefer `vtkSMPThreadLocalObject` to avoid manual lifecycle management.

- Scope: C++ sources using `vtkLabelMapLookup` in SMP parallel contexts
- Support: 3 MRs, 3 threads, 2019-12-16 to 2024-05-30
- Reviewers: michael.migliore (1), charles.gueunet (1), will.schroeder (1)
- [!11177](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11177) will.schroeder, 2024-05-30: "Spiros is correct, the vtkLabelMapLookup is meant to be used as a vtkSMPThreadLocal variable."
- [!10750](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10750) charles.gueunet, 2023-12-13: "To use this class in a smp parallel context, one has to create one instance per thread, using a `vtkSMPThreadLocal`."
- [!6240](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6240) michael.migliore, 2019-12-16: "Use `vtkSMPThreadLocalObject` where you can and remove manual life cycle management"

## correctness

### R068: Check for nullptr before dereferencing or using a pointer.

Rationale: To prevent undefined behavior or unintended state changes.

- Scope: C++ code (implied by nullptr checks and pointer usage in evidence)
- Support: 6 MRs, 7 threads, 2018-01-11 to 2025-05-14
- Reviewers: ken-martin (1), sebastien.jourdain (1), ben.boeckel (1), mwestphal (1), tiffany.chhim (1)
- [!12106](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12106) shreeraj.jadhav, 2025-05-14: "Do we need a `nullptr` check on any of the input parameters? Or do we expect them to be checked already in the call tree?"
- [!10509](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10509) thomas.galland, 2023-09-19: "Check for `nullptr` (can be)"
- [!9468](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9468) mwestphal, 2022-10-04: "`if (frequencies)` should be enough ?"

## testing

### R186: Tests must use `vtkTesting::GetTempDirectory()` and check that the returned directory is not null before using it, and all files written by tests must be rooted under the `-T` directory.

Rationale: Tests should use `vtkTesting::GetTempDirectory()` because it will fail on Windows otherwise.

- Scope: tests
- Support: 3 MRs, 3 threads, 2019-10-28 to 2023-07-21
- Reviewers: chuck.atkins (1), ben.boeckel (1), lucas.givord (1)
- [!10330](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10330) lucas.givord, 2023-07-21: "test availablity of the vtk_temp_dir before using it (so check that tempDir isn't null)"
- [!6304](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6304) ben.boeckel, 2019-12-23: "Tests should use `vtkTesting::GetTempDirectory`. This is going to fail on Windows otherwise."
- [!6084](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6084) chuck.atkins, 2019-10-28: "All files written by tests should be rooted under the `-T` directory (see `vtkTesting::GetTempDirectory()`)."

## design-architecture

### R216: Make class member variables private instead of protected.

Rationale: This helps with deprecation and future refactor by allowing members to be renamed or removed without needing compatibility code.

- Scope: C++ class member variables
- Support: 3 MRs, 3 threads, 2024-03-28 to 2026-01-26
- Reviewers: thomas.galland (1), nicolas.vuaille (1), spiros.tsalikis (1)
- [!12764](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12764) spiros.tsalikis, 2026-01-26: "Unless there's a reason subclasses need to directly access the members, making them private eases the deprecation policy for them (we can just rename/remove at will rather than having to bridge with c"
- [!11209](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11209) nicolas.vuaille, 2025-04-01: "Last, I advise to put all class members as private instead of protected: this helps a lot with deprecation and future refactor!"
- [!10995](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10995) thomas.galland, 2024-03-28: "I think we can consider setting it `private` and accessed through getters in subclasses (better for potential future depreciation IMO)"
