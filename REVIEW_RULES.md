# VTK review rules (draft)

Drafted automatically from VTK merge request reviews before 2026-01-01. Each rule groups conventions that reviewers stated in their own words across several merge requests (cosine distance 0.25). Nothing here is approved: a maintainer should accept, edit, merge, or reject each rule.

Every supporting comment was checked individually against the stated rule; comments about something else were removed from the support counts, and comments that disagree are listed as counter-evidence. A rule marked *mixed evidence* has at least one counter-example.

## style

### R002: Use `this->` prefix for all member variable and method access.

Rationale: Reviewers stated that `this->` is needed for member access and method calls.

- Scope: C++ sources
- Support: 27 MRs, 40 threads, 2017-01-26 to 2025-03-13
- Reviewers: jpouderoux (9), cory.quammen (5), charles.gueunet (5), mwestphal (3), michael.migliore (3)
- [!11971](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11971) acbauer, 2025-03-13: "Use `this->` for class members"
- [!11347](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11347) lucas.givord, 2024-07-24: "don't forget `this->` before using a class method (same remark for below)"
- [!9663](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9663) ben.boeckel, 2022-11-02: "Please use `this->` for all member accesses."

### R003: Use lowercase for local variable names.

*Mixed evidence: check the examples before accepting.*

Rationale: To distinguish local variables from member variables and follow the convention that local variables should start with a lowercase letter.

- Scope: C++ sources
- Support: 26 MRs, 28 threads, 2015-06-28 to 2025-12-09
- Reviewers: jpouderoux (5), cory.quammen (5), mwestphal (5), charles.gueunet (3), utkarsh.ayachit (2)
- [!12688](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12688) michael.migliore, 2025-12-09: "`Timestamp` is a single word so `S` should be lowercase."
- [!11449](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11449) charles.gueunet, 2024-09-02: "please, avoid starting a local variable with an uppercase, as this is reserved for class fields."
- [!10898](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10898) ben.boeckel, 2024-03-04: "Please use lowercase for local variables."
- Counter-evidence:
  - [!3482](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3482) aron.helser, 2017-10-25: "You should use camel case for variable names, probably?"
  - [!11233](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11233) lucas.givord, 2024-06-18: "variable shouldn't be named in snake case"
  - [!11903](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11903) louis.gombert, 2025-02-11: "Capitalize variable names like the ones above"

### R006: Use PascalCase for method names and camelCase for variable and data object names, avoiding abbreviations and ensuring descriptive, full-word naming.

*Mixed evidence: check the examples before accepting.*

Rationale: Reviewers stated that VTK coding guidelines require PascalCase for methods, camelCase for variables and data objects, and prohibit abbreviations to improve readability and searchability.

- Scope: all C++ sources
- Support: 23 MRs, 23 threads, 2015-05-01 to 2025-11-27
- Reviewers: cory.quammen (9), dgobbi (3), mwestphal (3), lucas.givord (2), aashish-chaudhary (1)
- [!12655](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12655) mwestphal, 2025-11-27: "is_success does not follow vtk guidelines to use camelCase"
- [!11884](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11884) mwestphal, 2025-01-30: "please rename this var"
- [!11725](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11725) lucas.givord, 2024-12-04: "you probably do too much python recently so that you use using snake_case variable in vtk, we should avoid that"
- Counter-evidence:
  - [!10587](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10587) thomas.galland, 2023-10-13: "maybe avoid using `vtk` prefix in variable names"
  - [!11971](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11971) acbauer, 2025-03-13: "Would prefer that all class member variables start with capital letter for VTK code formatting consistency"

### R007: Use vtkIdType instead of int for loop indices and variables related to cell counts, points, vertices, and array indices and sizes.

*Mixed evidence: check the examples before accepting.*

Rationale: To avoid implicit conversion issues, signed/unsigned comparison warnings, and to ensure compatibility with 64-bit builds.

- Scope: C++ sources
- Support: 21 MRs, 25 threads, 2017-01-18 to 2025-10-10
- Reviewers: jpouderoux (4), christos.tsolakis (4), utkarsh.ayachit (2), timothee.chabat (2), lucas.givord (2)
- [!12420](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12420) lucas.givord, 2025-10-10: "vtkIdType instead of int"
- [!12012](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12012) jaswant.panchumarti, 2025-04-18: "Use `vtkIdType` which can fit 64-bit integers when building for 64-bit."
- [!11305](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11305) will.schroeder, 2024-07-09: "The problem is with what kind of variable do you initialize it with, if it was ```auto i = this->NumberOfPoints``` it would work, ```auto i = 0``` does not work because 0 is an int."
- Counter-evidence:
  - [!9085](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9085) spiros.tsalikis, 2022-04-18: "The only suggestion that i have is that you can minimize the size of many structures by detecting if it's beneficial to always use vtkIdType (32 bits vs 64 bits)."

### R009: Place all variables and functions in an anonymous namespace and use the :: scope resolution operator when referencing them.

*Mixed evidence: check the examples before accepting.*

Rationale: To ensure uniqueness to the compilation unit.

- Scope: all C++ sources
- Support: 19 MRs, 22 threads, 2015-11-23 to 2025-10-28
- Reviewers: lucas.givord (7), yohann.bearzi (3), mwestphal (2), julien.fausty (2), thomas.galland (2)
- [!12311](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12311) lucas.givord, 2025-10-28: "should be in the anonymous namespace"
- [!12185](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12185) mathurin.lemarie, 2025-07-01: "This should be in an anonymous namespace"
- [!11483](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11483) lucas.givord, 2024-10-10: "when calling something in an anonymous namespace we always prefixed that with the ::"
- Counter-evidence:
  - [!3804](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3804) acbauer, 2018-01-18: "I'm not 100% sure on this but I think the VTK convention would be to have these method be camel case, e.g. `PErrorEOF`."
  - [!11824](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11824) sankhesh, 2025-01-15: "Could we please avoid anonymous namespace here? IMHO, these functions can be in a named vtkanari-specific namespace`."

### R010: Use static_cast for C-style casts in C++ code.

*Mixed evidence: check the examples before accepting.*

Rationale: The reviewers stated that static_cast should be used instead of C-style casts to improve type safety and avoid casting away constness without good reason.

- Scope: all C++ sources
- Support: 18 MRs, 19 threads, 2017-03-13 to 2025-07-24
- Reviewers: mwestphal (3), alouis (2), alliepiper16 (2), michael.migliore (2), yohann.bearzi (2)
- [!9207](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9207) timothee.chabat, 2022-05-23: "prefer static_cast over C cast"
- [!8884](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8884) seanm, 2022-02-04: "Should probably be `static_cast<vtkIdType>` now I think..."
- [!7946](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7946) ben.boeckel, 2021-05-07: "It's good style to use C++-style casts, and in particular constness should not be cast away without good reason. The only reason this source file used C-style casts is because it was written 20 years "
- Counter-evidence:
  - [!10958](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10958) charles.gueunet, 2024-03-14: "avoid C-style cast"

### R011: All VTK conditionals and loops must use curly braces.

Rationale: The evidence states that VTK style requires braces for conditionals and loops to conform to its coding style.

- Scope: all C++ sources
- Support: 18 MRs, 19 threads, 2015-09-10 to 2024-09-23
- Reviewers: dgobbi (4), ken-martin (4), cory.quammen (3), demarle (2), ben.boeckel (1)
- [!11506](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11506) dgobbi, 2024-09-23: "VTK code style includes `this` on method calls, and braces on if/for/while: ```c++ if (!this->EnsureGenericDisplay()) { return nullptr; } ```"
- [!11361](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11361) leon.victor, 2024-08-13: "vtk style enforces braces for all for loops"
- [!7521](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7521) cory.quammen, 2023-03-24: "VTK style requires braces {} for any conditional section."

### R012: Use nullptr for pointer initialization and comparisons, replacing NULL and 0 with nullptr.

*Mixed evidence: check the examples before accepting.*

Rationale: The reviewers stated that nullptr should be used instead of NULL, 0, or !ptr for pointer initialization and equality checks.

- Scope: all C++ sources
- Support: 17 MRs, 20 threads, 2017-06-13 to 2025-11-12
- Reviewers: ben.boeckel (5), cory.quammen (4), mwestphal (3), yohann.bearzi (2), robertmaynard (1)
- [!12021](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12021) mwestphal, 2025-03-28: "double* ShapeFunctionDerivativeWeights = nullptr;"
- [!11842](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11842) mwestphal, 2025-01-15: "vtkMultiProcessController* Controller = nullptr;"
- [!9519](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9519) ben.boeckel, 2022-09-01: "Please use `nullptr` instead of `NULL` in all C++ code."
- Counter-evidence:
  - [!1485](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1485) utkarsh.ayachit, 2016-05-12: "use `NULL` we so can grep-replace to `nullptr` when time comes."

### R013: Avoid using single-letter variable names unless they are standard for the associated math equation.

Rationale: Reviewers stated that single-letter variable names should be avoided unless they are standard for the associated math equation.

- Scope: all C++ sources
- Support: 16 MRs, 18 threads, 2021-08-13 to 2025-12-09
- Reviewers: mwestphal (14), thomas.galland (2), lucas.givord (2)
- [!12699](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12699) lucas.givord, 2025-12-09: "Generally, we should avoid using one letter for variable naming, could you please change that for `v`, `m` ?"
- [!12611](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12611) mwestphal, 2025-11-18: "avoid single letter var"
- [!12548](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12548) lucas.givord, 2025-10-23: "we should avoid acronym/one letter variable if it's possible"

### R014: Use `bool` instead of `vtkTypeBool` for new code and boolean member variables.

*Mixed evidence: check the examples before accepting.*

Rationale: vtkTypeBool is deprecated and bool can always be used instead.

- Scope: C++ sources
- Support: 15 MRs, 15 threads, 2018-11-29 to 2025-04-15
- Reviewers: utkarsh.ayachit (3), jpouderoux (2), mwestphal (2), borisb (1), ben.boeckel (1)
- [!12052](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12052) nicolas.vuaille, 2025-04-15: "we prefer using actual `bool` now. `vtkTypeBool` is the old style way to do."
- [!10366](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10366) mwestphal, 2023-07-27: "vtkTypeBool should be initialized with false/true instead"
- [!8967](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8967) cory.quammen, 2022-03-07: "Note that the long term plan is to transition boolean variables to `vtkTypeBool`, then flip the typedef for `vtkTypeBool` from `int` to `bool` at a major release. Any reason to jump ahead on this one "
- Counter-evidence:
  - [!1171](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1171) cory.quammen, 2016-02-03: "With respect to this change, I would recommend defining the VTK bool type format defined in Common/Core/vtkType.h and name the bool type vtkTypeBool. More verbose, yes, but it is at least consistent w"
  - [!1171](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1171) lorensen, 2016-07-08: "I agree with Cory that the new type should be vtkTypeBool to be consistent with most of the types in vtkType.h"
  - [!5806](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5806) michael.migliore, 2019-08-01: "add boolean macros"

### R015: Use curly braces for all control flow blocks, including if, else, for, and while statements, even when they contain only a single line.

Rationale: Curly braces are required by style for safety and readability, as stated by multiple reviewers.

- Scope: all C++ sources
- Support: 15 MRs, 15 threads, 2016-01-12 to 2022-02-15
- Reviewers: lorensen (2), jpouderoux (2), sebastienbarre (1), mwestphal (1), alliepiper16 (1)
- [!7806](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7806) cory.quammen, 2021-04-02: "Curly braces needed for both true and false branches."
- [!7039](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7039) utkarsh.ayachit, 2020-06-22: "minor style: use `{}` after `if`."
- [!6782](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6782) ben.boeckel, 2020-04-21: "They are required by style, but not present everywhere in VTK."

### R016: Replace all std::cerr, std::cout, std::endl, and direct cerr writes with appropriate VTK logging macros such as vtkLogF, vtkWarningMacro, vtkErrorMacro, vtkGenericWarningMacro, vtkDebugWithObjectMacro, or vtkLog.

Rationale: VTK logging macros enable easier error capture and consistent logging across the codebase.

- Scope: all C++ sources
- Support: 15 MRs, 15 threads, 2016-10-26 to 2025-12-10
- Reviewers: mwestphal (4), utkarsh.ayachit (2), cory.quammen (2), ben.boeckel (2), lorensen (1)
- [!12321](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12321) spiros.tsalikis, 2025-12-10: "replace std::cerr everywhere with vtkLogF like you do below"
- [!11543](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11543) berkgeveci, 2024-10-17: "Please use vtkErrorMacro() rather than directly writing to cerr. This enables us to capture errors more easily in applications."
- [!10324](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10324) ben.boeckel, 2023-07-08: "cout? vtkLogger is probably better to use here (and elsewhere in the file). Yeah...most occurrences of cout should've been converted to vtkDebugWithObjectMacro."

### R017: All class members should be private unless there is a specific reason for subclasses to access them, in which case they should be protected or accessed via an accessor.

*Mixed evidence: check the examples before accepting.*

Rationale: Subclasses should not need direct access to members, and any required access should be provided through protected members or accessors.

- Scope: C++ class members
- Support: 13 MRs, 13 threads, 2019-02-15 to 2025-11-13
- Reviewers: mwestphal (10), jpouderoux (1), ben.boeckel (1), nicolas.vuaille (1)
- [!12611](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12611) mwestphal, 2025-11-13: "every menbers should be private"
- [!12311](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12311) mwestphal, 2025-10-21: "I am moving it to the private section"
- [!11424](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11424) mwestphal, 2024-08-26: "members should be private"
- Counter-evidence:
  - [!11079](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11079) mwestphal, 2024-04-24: "Only the variable Stream should be private."

### R018: Remove commented code and uncomment code that is not currently in use.

Rationale: The reviewers stated that commented-out code should be removed and code that is not currently in use should be uncommented or removed.

- Scope: all C++ sources
- Support: 13 MRs, 14 threads, 2017-02-21 to 2025-09-01
- Reviewers: mwestphal (3), tjcorona (2), ben.boeckel (1), demarle (1), jpouderoux (1)
- [!11708](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11708) thomas.galland, 2024-12-16: "here and bellow: remove commented code"
- [!10397](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10397) nicolas.vuaille, 2023-08-09: "Why this info ? Is there another way to setup the filter? Right, I'll remove it as there are no other way to add values to vectors"
- [!9812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9812) julien.fausty, 2023-04-20: "Please remove commented code"

### R020: Initialize member variables in the constructor initializer list.

Rationale: The reviewers stated that using an initializer list is preferred over assignment in the function body or in-class initializers.

- Scope: C++ source files
- Support: 12 MRs, 12 threads, 2019-05-07 to 2025-09-24
- Reviewers: mwestphal (3), sebastien.jourdain (1), florian.chevassu (1), yohann.bearzi (1), nicolas.vuaille (1)
- [!11844](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11844) mwestphal, 2025-01-17: "you can init the value here. ```suggestion:-0+0 bool EnableTouchEventProcessing = true; ```"
- [!10223](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10223) thomas.galland, 2023-05-24: "Here and bellow: : `this->TranslationAxis = Axis::NONE` -> `: Axis::NONE` ? (seems you are double assigning here, or I misunderstand something)"
- [!9193](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9193) timothee.chabat, 2022-05-18: "you can just add `, CustomSubdivisions(2, 2)` to the class initializer list"

### R022: Use the override keyword instead of the virtual keyword for overriding virtual functions.

*Mixed evidence: check the examples before accepting.*

Rationale: The reviewers stated that using virtual with override is redundant and that the virtual keyword can be dropped when override is present.

- Scope: C++ source files
- Support: 11 MRs, 12 threads, 2018-02-12 to 2024-06-18
- Reviewers: mwestphal (4), jpouderoux (2), robertmaynard (2), michael.migliore (1), charles.gueunet (1)
- [!10981](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10981) mwestphal, 2024-03-22: "virtual should not be here at the same time as override (true in the whole file btw)"
- [!10324](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10324) ben.boeckel, 2023-07-08: "`virtual override` is redundant. `clang-tidy` points this out"
- [!8475](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8475) mwestphal, 2021-12-19: "'GetActors' overrides a member function but is not marked 'override'"
- Counter-evidence:
  - [!8163](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8163) mwestphal, 2021-07-21: "remove all virtuals"
  - [!8163](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8163) mwestphal, 2021-07-21: "remove virtual"
  - [!8163](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8163) mwestphal, 2021-07-21: "remove virtuals"

### R023: Prefix all member variable and method access with `this->` in VTK code.

Rationale: To match VTK's coding style and ensure consistency.

- Scope: All C++ sources
- Support: 11 MRs, 11 threads, 2017-09-18 to 2025-11-19
- Reviewers: cory.quammen (3), demarle (2), mwestphal (2), dgobbi (1), sujin.philip (1)
- [!11247](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11247) cory.quammen, 2024-07-12: "Use `this->` per VTK style guidelines."
- [!8405](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8405) cory.quammen, 2021-09-17: "VTK style - prefix internal member access with `this->`"
- [!7247](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7247) yohann.bearzi, 2020-09-21: "Every attributes of the class should have `this->` suffix to match VTK's code practices."

### R024: Use range-based for loops instead of index-based or iterator-based loops when iterating over containers.

*Mixed evidence: check the examples before accepting.*

Rationale: Reviewers stated that range-based for loops are clearer and avoid explicit iterator declarations or index usage when the index is not needed.

- Scope: C++ source files
- Support: 10 MRs, 16 threads, 2019-08-01 to 2025-11-18
- Reviewers: utkarsh.ayachit (4), mwestphal (3), mzeyen (2), spiros.tsalikis (2), jaswant.panchumarti (2)
- [!12611](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12611) mwestphal, 2025-11-18: "-0+0 for (vtkLineRepresentation* lineRepresentation : LineRepresentationVector)"
- [!10587](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10587) charly.bollinger, 2023-10-12: "for (const auto& block : blocks) iterator loop here and below? unless you explicitly need the index"
- [!9812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9812) spiros.tsalikis, 2023-05-15: "change the for loop to ```for (const auto& cellPoint : cellPointSet) { cellArray->InsertCellPoint(cellPoint); }```"
- Counter-evidence:
  - [!6203](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6203) ken-martin, 2019-11-22: "Coding like for (i = 0; i < 47; i++) xCoords->InsertNextValue(x[i]); Is more error prone which is why we prohibited it in the first place."
  - [!8405](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8405) cory.quammen, 2021-09-13: "It's totally okay, preferred even."
  - [!10587](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10587) charly.bollinger, 2023-10-11: "could be replaced with iterator loop `for (const auto& result : results`"

### R025: Use std::size_t for all size and loop index variables.

Rationale: To avoid signed/unsigned comparison warnings and ensure consistent type usage.

- Scope: all C++ sources
- Support: 10 MRs, 13 threads, 2018-05-02 to 2025-05-06
- Reviewers: lucas.givord (6), cory.quammen (2), jaswant.panchumarti (2), jpouderoux (1), dgobbi (1)
- [!12088](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12088) lucas.givord, 2025-05-06: "we should always put the namespace, so in this case we need to change `size_t` to `std::size_t`"
- [!11986](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11986) mwestphal, 2025-03-28: "please check every use"
- [!11380](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11380) lucas.givord, 2024-08-09: "use std::size_t (here and everywhere)"

### R026: Initialize member variables in the header file.

*Mixed evidence: check the examples before accepting.*

Rationale: The reviewers stated that initializing members in the header is the preferred or modern way to improve the code.

- Scope: C++ source files
- Support: 9 MRs, 9 threads, 2019-05-28 to 2025-11-18
- Reviewers: mwestphal (7), timothee.chabat (1), guillaume.gisbert (1)
- [!12611](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12611) guillaume.gisbert, 2025-11-18: "init in header same with this->WidgetState"
- [!12459](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12459) mwestphal, 2025-09-29: "lets initi this in the header too :smile:"
- [!11073](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11073) mwestphal, 2024-04-22: "good occasion to move members initialization to the header."
- Counter-evidence:
  - [!8470](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8470) mwestphal, 2021-10-18: "I don't see many (or maybe any?) cases where we initialize member variables using _SafeDownCast_ in the header, so my feeling is initialization should remain in the source file."

### R029: Sort includes alphabetically.

Rationale: The reviewers stated that includes should be sorted alphabetically to maintain order.

- Scope: C++ sources
- Support: 9 MRs, 10 threads, 2016-12-05 to 2025-11-19
- Reviewers: mwestphal (4), demarle (3), alouis (2), mzeyen (1)
- [!5824](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5824) mzeyen, 2019-08-19: "Includes are not ordered alphabetically"
- [!2937](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2937) alouis, 2017-06-19: "Please sort includes by alphabetical order"
- [!2513](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2513) alouis, 2017-03-21: "Please sort includes by alphabetical order"

### R033: Use const std::string& for string parameters and std::string instead of raw const char* or char* for string manipulation and member variables to avoid copying and nullptr checks.

*Mixed evidence: check the examples before accepting.*

Rationale: To avoid unnecessary copies and the need to check for nullptr each time.

- Scope: C++ sources
- Support: 8 MRs, 9 threads, 2019-05-24 to 2025-12-09
- Reviewers: michael.migliore (2), mwestphal (2), seanm (1), cory.quammen (1), charles.gueunet (1)
- [!11129](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11129) louis.gombert, 2024-05-30: "working with only `std::string` here and in the function below would be easier and avoid conversions"
- [!9346](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9346) charles.gueunet, 2022-07-05: "may you use a string ? this would avoid the need to check agains `nullptr` each time."
- [!8503](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8503) mwestphal, 2021-10-08: "you can use std::string (and the adequate macro)"
- Counter-evidence:
  - [!5096](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5096) ken-martin, 2019-01-28: "As uniform calls can happen a lot in the inner loop that can be a bottleneck. In this MR https://gitlab.kitware.com/vtk/vtk/merge_requests/1898/diffs I switched from std::string to const char * and ou"
  - [!5377](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5377) mwestphal, 2019-05-06: "useless std::string"
  - [!5377](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5377) mwestphal, 2019-05-06: "useless std::string"

### R035: PrintSelf should call the superclass PrintSelf method before printing the class' own members.

*Mixed evidence: check the examples before accepting.*

Rationale: to ensure the superclass state is printed first and to not forget to check if something useful can be printed.

- Scope: all C++ sources
- Support: 8 MRs, 8 threads, 2016-09-06 to 2024-11-13
- Reviewers: mwestphal (2), utkarsh.ayachit (1), tiffany.chhim (1), christos.tsolakis (1), jcfr (1)
- [!10302](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10302) lucas.givord, 2023-07-18: "the `Superclass::PrintSelf` should be the first print called in this method"
- [!10227](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10227) charly.bollinger, 2023-06-06: "Seems VTK classes should always override the PrintSelf method (this is one of the `header checks` done in the CI), even if there is nothing more to print. I think this is done in order to not forget t"
- [!10163](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10163) jcfr, 2023-04-26: "1. All subclasses of `vtkObject` should include a `PrintSelf()` method that prints all publicly accessible ivars."
- Counter-evidence:
  - [!366](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/366) utkarsh.ayachit, 2015-07-14: "I think PrintSelf should not be calling GetWorldPosition. We don't call things that have side effects in PrintSelf. It's intended to dump the state of iVars, not update them."
  - [!11165](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11165) thomas.galland, 2024-05-29: "For internal members being vtk classes, I think you could call `Printself` on them recursively"

### R039: Adhere to VTK style guidelines for spacing, braces, indentation, and comments.

Rationale: Reviewers stated that code must follow VTK style guidelines to ensure consistency and readability.

- Scope: all C++ sources
- Support: 8 MRs, 8 threads, 2016-07-18 to 2021-01-28
- Reviewers: jpouderoux (2), will.schroeder (1), utkarsh.ayachit (1), demarle (1), alliepiper16 (1)
- [!7569](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7569) jcfr, 2021-01-28: "suggestion auto inTuples = vtk::DataArrayTupleRange<3>(pts, ptId, endPtId);"
- [!6604](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6604) finetjul, 2020-03-20: "VTK standard is : `//--------------------------------------------------------------------------`. I will add it."
- [!4909](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4909) jpouderoux, 2018-11-21: "there are still plenty of { at the end of a line of code. Please respect VTK style."

### R041: Remove empty lines, leaving only one empty line where needed.

*Mixed evidence: check the examples before accepting.*

Rationale: Reviewers stated that empty lines should be removed or reduced to a single line.

- Scope: C++ sources
- Support: 8 MRs, 8 threads, 2017-10-02 to 2025-05-23
- Reviewers: mwestphal (4), LucasGandelKitware (1), michael.migliore (1), jcfr (1), nicolas.vuaille (1)
- [!12107](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12107) mwestphal, 2025-05-23: "lets remove the supplementary empty lines ?"
- [!10164](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10164) jcfr, 2023-05-01: "Only have one empty line"
- [!4326](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4326) LucasGandelKitware, 2018-05-31: "leave just one empty line"
- Counter-evidence:
  - [!4909](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4909) michael.migliore, 2018-11-22: "remove two extra empty lines"

### R042: Use vtkSetMacro and vtkGetMacro for property accessors in C++ classes.

Rationale: Using macros makes clear that setters and getters are standard, not special, and avoids manual implementations.

- Scope: C++ sources
- Support: 8 MRs, 8 threads, 2018-03-28 to 2025-04-04
- Reviewers: jpouderoux (2), utkarsh.ayachit (2), michael.migliore (1), mwestphal (1), julia.sanchez (1)
- [!11988](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11988) lucas.givord, 2025-04-04: "we use a vtk macro for this one"
- [!10017](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10017) julia.sanchez, 2023-03-01: "vtkSetMacro(SearchMode, NeighborSearchMode); vtkGetMacro(SearchMode, NeighborSearchMode);"
- [!7994](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7994) utkarsh.ayachit, 2021-05-21: "VTK style for such methods is as follows: ```c++ // in .h void SetParmetricFunction(vtkParametricFunction*); vtkGetObjectMacro(ParametricFunction, vtkParametricFunction); ... vtkParametricFunction* Pa"

### R043: Use = default for special member functions in the class definition.

Rationale: The evidence states that = default is preferred for special member functions and that clang-tidy will flag otherwise.

- Scope: C++ sources
- Support: 8 MRs, 9 threads, 2018-04-03 to 2025-12-08
- Reviewers: mwestphal (3), ben.boeckel (2), jpouderoux (1), sujin.philip (1), michael.migliore (1)
- [!9487](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9487) ben.boeckel, 2022-09-01: "`clang-tidy` will want this (and other things) to be `= default`."
- [!7753](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7753) ben.boeckel, 2021-03-16: "`= default`. I'll leave the `clang-tidy` CI job to find anything else like this."
- [!6212](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6212) michael.migliore, 2019-11-20: "remove this line and use `= default` in the header"

### R044: Use double quotes for VTK headers instead of angle brackets and alphabetize all includes with a blank line between VTK and system headers.

*Mixed evidence: check the examples before accepting.*

Rationale: The reviewers stated that using double quotes instead of angle brackets is the established convention for VTK headers and that alphabetizing includes improves merge smoothness and consistency.

- Scope: all C++ sources
- Support: 7 MRs, 7 threads, 2017-03-13 to 2021-06-07
- Reviewers: mwestphal (2), yohann.bearzi (2), demarle (1), todoooo (1), ben.boeckel (1)
- [!8054](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8054) ben.boeckel, 2021-06-07: "Why is this using `<>` and not `""` like all of the other VTK headers?"
- [!5930](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5930) mwestphal, 2021-04-20: "Each include in VTK needs a justification, something like this: #include "vtkContextItem.h" #include "vtkInteractionWidgetsModule.h" // Needed for bla #include "vtkNew.h" // Needed for vtkNew #include"
- [!7213](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7213) yohann.bearzi, 2020-09-04: "The convention is to use "vtkSomething.h" instead of <vtkSomething.h>. Same remark goes for the test."
- Counter-evidence:
  - [!730](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/730) cory.quammen, 2015-10-12: "vtkIOGeometry-HeaderTest is failing because you are including <map> in the header file. This is disallowed according to item 27 in The VTK Software Process [1]."
  - [!4112](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4112) aashish-chaudhary, 2018-03-27: "just to be consistent you want to use < brackets and not ""
  - [!10587](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10587) charly.bollinger, 2023-10-12: "no need to separate vtkX includes imo"

### R049: Prefer std::array over C-style arrays for fixed-size collections.

Rationale: It simplifies algorithms and avoids naming confusion.

- Scope: C++ sources
- Support: 7 MRs, 7 threads, 2018-05-02 to 2025-09-29
- Reviewers: jpouderoux (1), ben.boeckel (1), timothee.chabat (1), florian360 (1), charles.gueunet (1)
- [!12455](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12455) guillaume.gisbert, 2025-09-29: "i feel like it could be replaced with a std::array. This could simplify some algorithms like GetClassNameFromTypeId when computing table length, or looping over indices and not comparing to nullptr"
- [!11358](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11358) leon.victor, 2024-08-02: "If the size is static use an `std::array`"
- [!10948](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10948) charles.gueunet, 2024-03-12: "std array here and below (fixed size, known at compile time)"

### R052: Use vtkSetClampMacro for enum values to restrict valid inputs and specify default, minimum, and maximum values in the description.

*Mixed evidence: check the examples before accepting.*

Rationale: The reviewers stated that vtkSetClampMacro should be used to limit the possible values of enum parameters and to specify acceptable ranges.

- Scope: C++ source files
- Support: 6 MRs, 8 threads, 2015-06-29 to 2022-05-12
- Reviewers: utkarsh.ayachit (4), acbauer (2), jpouderoux (1), tiffany.chhim (1)
- [!9179](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9179) tiffany.chhim, 2022-05-12: "vtkSetClampMacro(VectorScaleMode, int, SCALE_BY_MAGNITUDE, SCALE_BY_COMPONENTS); vtkGetMacro(VectorScaleMode, int);"
- [!8408](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8408) utkarsh.ayachit, 2021-09-13: "please the enum for range. `vtkSetClampMacro(Mode, int, vtkPartitionBalancer::Expand, vtkPartitionBalancer::Squash`."
- [!7994](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7994) utkarsh.ayachit, 2021-05-21: "Use `vtkSetClampMacro(NumberOfPartitions, int, 0, VTK_INT_MAX);`"
- Counter-evidence:
  - [!12500](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12500) nicolas.vuaille, 2025-10-07: "I follow what the macro do previously (define a virtual setter, getter for min, getter for max), because I need to forward the BoundaryMode set by the user internally"

### R054: Use const auto& for loop variables to avoid unnecessary copies.

*Mixed evidence: check the examples before accepting.*

Rationale: to avoid the overhead of calling the copy constructor for each element.

- Scope: C++ source files
- Support: 6 MRs, 9 threads, 2018-12-19 to 2025-12-13
- Reviewers: timothee.chabat (5), robertmaynard (1), yohann.bearzi (1), sankhesh (1), jaswant.panchumarti (1)
- [!9231](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9231) timothee.chabat, 2022-06-07: "here and above, `const auto&` if tou don't change the value (and if possible)"
- [!5002](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5002) robertmaynard, 2018-12-19: "I would say this would be a perfect place for `auto`. ```cpp auto ldEnd = this->LocalData.end(); for (auto ldItr=this->LocalData.begin(); ldItr != ldEnd; ++ldItr ) { ... } ```"
- [!12237](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12237) jaswant.panchumarti, 2025-12-13: suggested `for (const auto& id : ids)`
- Counter-evidence:
  - [!9042](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9042) charles.gueunet, 2022-04-05: suggested `std::copy(this->TimeStepIndices.cbegin(), this->TimeStepIndices.cend(), timeStepIndices);`

### R056: Use spaces around operators in foreach/if conditions and in parameter lists.

Rationale: Reviewers stated that spaces improve consistency and readability of code.

- Scope: CMake files
- Support: 6 MRs, 6 threads, 2016-12-06 to 2025-11-25
- Reviewers: mwestphal (2), jpouderoux (1), dgobbi (1), jcfr (1), ben.boeckel (1)
- [!12526](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12526) ben.boeckel, 2025-11-25: "foreach (comp IN LISTS VTK_AVAILABLE_COMPONENTS) if(comp IN_LIST skipped_components) continue () endif () if (NOT VTK_${comp}_FOUND) message (SEND_ERROR "Expected VTK component \"${comp}\" could not b"
- [!4087](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4087) jcfr, 2018-03-20: "Consistently use spaces: `i=-baseCube` or `i = -baseCube`"
- [!3647](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3647) mwestphal, 2018-01-08: "spaces, here and everywhere"

### R057: Use EXIT_SUCCESS and EXIT_FAILURE instead of integer literals or exit() in return statements.

Rationale: The reviewers stated that using EXIT_SUCCESS/EXIT_FAILURE makes return codes explicit and avoids integer literals or exit() calls.

- Scope: C++ sources
- Support: 6 MRs, 6 threads, 2016-12-16 to 2023-10-06
- Reviewers: ben.boeckel (2), lorensen (1), utkarsh.ayachit (1), julien.fausty (1), charly.bollinger (1)
- [!10567](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10567) charly.bollinger, 2023-10-06: "here and below, `return EXIT_FAILURE` instead of `false`"
- [!10501](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10501) julien.fausty, 2023-09-12: "prefer EXIT_SUCCESS/EXIT_FAILURE for explicitness"
- [!10081](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10081) ben.boeckel, 2023-04-24: "Please use `EXIT_FAILURE` and `EXIT_SUCCESS` here."

### R060: Do not perform a null check before calling Delete() on a pointer.

Rationale: The evidence states that delete (including delete[]) is safe with nullptr and therefore null checks are unnecessary and redundant.

- Scope: C++ sources
- Support: 6 MRs, 6 threads, 2017-07-10 to 2025-05-01
- Reviewers: dgobbi (1), mwestphal (1), jpouderoux (1), demarle (1), ben.boeckel (1)
- [!12095](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12095) jaswant.panchumarti, 2025-05-01: "null check needed since `PickList` now has a setter. can you check the same in other places as well? ```suggestion:-0+0 if (this->PickList != nullptr) { this->PickList->Delete(); } ```"
- [!8332](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8332) ben.boeckel, 2021-08-24: "There's no need to guard `delete` with a `nullptr` check."
- [!6508](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6508) demarle, 2020-04-10: "To the best of my knowledge, checking for null before delete is unnecessary and redundant. https://github.com/ospray/ospray/blob/master/ospray/api/API.cpp#L541 Same goes with c++ delete, delete(nullpt"

### R061: Use bool for boolean variables and replace int with bool for boolean flags.

Rationale: Reviewers stated that bool is preferred for boolean variables and flags in new code.

- Scope: C++ sources
- Support: 6 MRs, 10 threads, 2017-08-18 to 2022-11-08
- Reviewers: christos.tsolakis (6), timothee.chabat (2), jpouderoux (1), cory.quammen (1)
- [!9626](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9626) christos.tsolakis, 2022-11-08: "`bool abort = false;`"
- [!9531](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9531) christos.tsolakis, 2022-09-19: "should be `bool abort = false`."
- [!9270](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9270) christos.tsolakis, 2022-08-04: "same here , replace `int` with `bool`"

### R071: Prefer explicit type declarations over `auto` when the type is not explicitly stated in the expression or is not obvious from context.

Rationale: The reviewers stated that `auto` obscures the type and makes it harder to understand the code, especially when the type changes meaning or is not evident from the right-hand side.

- Scope: all C++ sources
- Support: 6 MRs, 6 threads, 2021-02-16 to 2024-03-12
- Reviewers: charles.gueunet (3), LucasGandelKitware (1), mwestphal (1), scott.wittenburg (1)
- [!10948](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10948) charles.gueunet, 2024-03-12: "I find better to have the exact type on the left side when not already explicit on the right side of the expression"
- [!9636](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9636) scott.wittenburg, 2022-10-20: "I agree, many times auto obscures the type of the object - you need to navigate to the function returning the object to figure this out. I try to only use auto for iterators but sometimes I may slip a"
- [!9170](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9170) charles.gueunet, 2022-05-11: "`auto` when the type is not explicit is not recommanded"

### R074: Initialize pointers to nullptr directly or via default member initializers to prevent invalid delete of uninitialized pointers.

*Mixed evidence: check the examples before accepting.*

Rationale: to prevent invalid delete of uninitialized pointer

- Scope: C++ sources
- Support: 5 MRs, 5 threads, 2017-12-14 to 2024-08-01
- Reviewers: utkarsh.ayachit (1), mwestphal (1), cory.quammen (1), lucas.givord (1), louis.gombert (1)
- [!11330](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11330) louis.gombert, 2024-08-01: "you can init to `nullptr` here directly"
- [!11271](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11271) lucas.givord, 2024-07-05: "init pointer to nullptr here and below"
- [!5930](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5930) mwestphal, 2021-03-22: "In any case, this should read at least: `vtkContextTransform* Transform = nullptr;`"
- Counter-evidence:
  - [!5588](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5588) nicolas.vuaille, 2019-08-19: "`= nullptr` : not consistent with `Texture` member, that is initialized in constructor."
  - [!10914](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10914) nicolas.vuaille, 2024-03-11: "should probably not default to nullptr. Same for other arg"

### R075: Prefer early returns or guard clauses over nested if-return patterns and avoid using else when the if block already handles the return or necessary logic.

*Mixed evidence: check the examples before accepting.*

Rationale: This improves readability by reducing nesting and clarifies control flow.

- Scope: C++ sources
- Support: 5 MRs, 5 threads, 2018-02-12 to 2025-07-23
- Reviewers: mwestphal (2), julien.fausty (1), lucas.givord (1), louis.gombert (1)
- [!12305](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12305) louis.gombert, 2025-07-23: "instead of `if: return if: return ... raise()` you can do `if: ... elif: ... else: raise()`"
- [!10353](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10353) lucas.givord, 2023-07-26: "you don't need to do it in a else section here"
- [!9792](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9792) julien.fausty, 2023-01-04: "could we do a `else if(this->SearchMethod == vtkPiecewiseFunction::InterpolationSearch)` and then have the `else` block be some error handling? Also, you can return directly from inside the conditiona"
- Counter-evidence:
  - [!7607](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7607) utkarsh.ayachit, 2021-02-10: "I'd rewrite this...insert line 1162 at 1151 instead and then leave the else unchanged."

### R083: Headers should be sorted alphabetically.

Rationale: The reviewers stated that headers are not ordered and should be sorted.

- Scope: C++ sources
- Support: 5 MRs, 9 threads, 2018-01-25 to 2023-06-02
- Reviewers: michael.migliore (8), ben.boeckel (1)
- [!10253](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10253) ben.boeckel, 2023-06-02: "Same here: should be sorted. Or have a newline to separate into sections (maybe with a comment)."
- [!6812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6812) michael.migliore, 2020-04-30: "avoid empty lines between headers, and sort them"
- [!3816](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3816) michael.migliore, 2018-01-25: "headers are not ordered"

### R092: Do not rely on headers providing standard library includes; include standard library headers in the header file, not just the implementation file.

*Mixed evidence: check the examples before accepting.*

Rationale: Missing standard library includes can cause compilation errors on certain compilers/versions, and including STL headers in header files can slow down compilation time.

- Scope: all C++ sources
- Support: 4 MRs, 4 threads, 2015-10-27 to 2024-03-15
- Reviewers: cory.quammen (1), ken-martin (1), lucas.givord (1), ben.boeckel (1)
- [!10969](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10969) ben.boeckel, 2024-03-15: "Why is this removed? We try not to rely on the header providing things like this."
- [!10302](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10302) lucas.givord, 2023-07-18: "please add `#include <array>` here instead of in the cxx"
- [!8510](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8510) ken-martin, 2021-11-02: "I believe std::isdigit requires cctype which is not included. Adding the include for cctype fixes the compile error."
- Counter-evidence:
  - [!137](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/137) robertmaynard, 2015-04-28: "Since they are not part of the C++ 98 standard I am against using them as we shouldn't rely on non standard headers or features unless absolutely necessary."

### R095: Use the ternary operator for simple conditional assignments and logic.

*Mixed evidence: check the examples before accepting.*

Rationale: The reviewers stated that the ternary operator should be used to simplify conditional logic and reduce lines of code.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2020-05-29 to 2025-09-26
- Reviewers: jpouderoux (1), charles.gueunet (1), julien.fausty (1), timothee.couble (1)
- [!10233](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10233) julien.fausty, 2023-08-07: "if (!this->CellInterfaceType) { // case intermediate interface with A and B processLeafCellWithDoubleInterface(cursor, scalarsInterfaceA, scalarsInterfaceB); } // case type == 1 just "right" interface"
- [!9567](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9567) charles.gueunet, 2022-09-23: "topology = polyOutput ? polyOutput->GetPolys() : ugOutput->GetCells();"
- [!12459](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12459) timothee.couble, 2025-09-26: suggested `if (auto cx = md.findChild("offset_x"); cx.valid()) { ox = cx.value<double>(); }`
- Counter-evidence:
  - [!11424](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11424) lucas.givord, 2024-08-26: "I believe nested ternary operation is bad for readability, could you please split that?"

### R096: Rename variables to avoid shadowing class names or causing shadowing warnings.

Rationale: Shadowing variables triggers warnings in nightly testing.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2015-09-04 to 2023-11-22
- Reviewers: cory.quammen (1), dgobbi (1), utkarsh.ayachit (1), lucas.givord (1)
- [!10717](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10717) lucas.givord, 2023-11-22: "we should rename this variable `unstructuredGrid` or something like that :slight_smile:"
- [!7607](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7607) utkarsh.ayachit, 2021-02-17: "warning C4456: declaration of 'mpf' hides previous local declaration"
- [!2309](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2309) dgobbi, 2017-01-10: "Shadowing is forbidden because it triggers warnings in our nightly testing."

### R098: Move variable declarations to the innermost block or line where the variable is first used.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2016-12-06 to 2021-11-12
- Reviewers: jpouderoux (2), michael.migliore (1), dgobbi (1)
- [!8635](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8635) dgobbi, 2021-11-12: "move the `cfinfo` declaration to the inside of the block where `cfinfo` is used"
- [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) michael.migliore, 2020-03-06: "move variable declaration to line where it is used"
- [!4927](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4927) jpouderoux, 2018-11-28: "move variables where they are used"

### R100: Order directories and files alphabetically for readability.

Rationale: To improve readability.

- Scope: directories and files
- Support: 4 MRs, 4 threads, 2017-09-11 to 2024-06-24
- Reviewers: acbauer (1), tiffany.chhim (1), ben.boeckel (1), nicolas.vuaille (1)
- [!11254](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11254) nicolas.vuaille, 2024-06-24: "maybe order alphabetically for readability"
- [!10879](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10879) ben.boeckel, 2024-02-26: "Now all directories should be ordered."
- [!9232](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9232) tiffany.chhim, 2022-06-01: "Try to keep alphabetical order."

### R104: Remove dead code that is no longer needed.

Rationale: The reviewers stated that the code is no longer used or needed and should be removed.

- Scope: all C++ sources
- Support: 4 MRs, 4 threads, 2018-04-18 to 2024-12-09
- Reviewers: mwestphal (2), dgobbi (1), lucas.givord (1)
- [!11695](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11695) lucas.givord, 2024-12-09: "Looks like we don't anymore"
- [!8675](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8675) mwestphal, 2021-12-27: "Please remove all dead code."
- [!4201](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4201) dgobbi, 2018-04-18: "The change looks good except for the `if False:`. Please just remove the old code, there's really no reason to keep it considering the checks that you have in place."

### R105: Place opening and closing braces on their own lines.

Rationale: The reviewers stated that braces must be on a new line to respect VTK style.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2018-11-21 to 2019-11-18
- Reviewers: jpouderoux (2), ken-martin (1), utkarsh.ayachit (1)
- [!6209](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6209) utkarsh.ayachit, 2019-11-18: "incorrect `{`...must be on a new line."
- [!5439](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5439) jpouderoux, 2019-04-18: "bad style ('{' should be on its line)"
- [!5380](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5380) ken-martin, 2019-04-09: "Style, braces on a separate line"

### R108: Class names should be in alphabetical order.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2019-10-14 to 2024-02-07
- Reviewers: yohann.bearzi (2), ben.boeckel (1), nicolas.vuaille (1)
- [!6609](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6609) yohann.bearzi, 2020-03-23: "Those class name need to be sorted in alphabetical order."
- [!6066](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6066) yohann.bearzi, 2019-10-14: "`class` names should be in alphabetical order."
- [!10869](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10869) nicolas.vuaille, 2024-02-07: "alphabetical order"

### R110: Use clang-format off/on blocks to suppress formatting for specific code sections.

Rationale: To prevent formatting tools from altering code that requires specific spacing, includes, or layout that would otherwise break compilation or manual formatting.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2019-12-02 to 2024-03-04
- Reviewers: ben.boeckel (1), utkarsh.ayachit (1), mwestphal (1), jaswant.panchumarti (1)
- [!10898](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10898) jaswant.panchumarti, 2024-03-04: "missing clang-format off...clang-format on"
- [!9505](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9505) mwestphal, 2022-08-30: "maybe disable clang format on this file ? ... done, with the original formatting kept"
- [!7507](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7507) utkarsh.ayachit, 2021-01-06: "add `/* clang-format off */` ... `/* clang-format on */` around these to avoid clang format from messing with the spacing ...this won't compile otherwise."

### R113: Initialize all members in the header to provide default values

Rationale: to provide default values

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2020-05-24 to 2024-05-14
- Reviewers: mwestphal (3), charles.gueunet (1)
- [!11120](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11120) mwestphal, 2024-05-14: "you could initialize that in the header"
- [!10072](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10072) mwestphal, 2023-03-28: "init all members in header"
- [!9193](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9193) charles.gueunet, 2022-05-20: "Initialize all you can in the header to provide default values"

### R114: Use this->Superclass::MethodName when calling a superclass method.

Rationale: To keep the intent clear.

- Scope: C++ sources
- Support: 4 MRs, 5 threads, 2020-07-13 to 2025-03-17
- Reviewers: utkarsh.ayachit (4), mwestphal (1)
- [!7844](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7844) utkarsh.ayachit, 2021-04-13: "If you're simply calling superclass, use `this->Superclass::GetCellNeighbors`; that keeps the intent clear."
- [!7101](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7101) utkarsh.ayachit, 2020-07-13: "all calls to `Superclass::...` must be written as `this->Superclass::...`"
- [!11957](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11957) mwestphal, 2025-03-17: suggested `this->Superclass::SetNumberOfInputPorts(1);`

### R115: Declare constexpr variables as static and name them in ALL_CAPS.

Rationale: Reviewers stated that constexpr variables should be static and named in ALL_CAPS.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2021-01-22 to 2025-04-08
- Reviewers: mwestphal (2), ben.boeckel (1), nicolas.vuaille (1)
- [!12021](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12021) mwestphal, 2025-04-08: "all these should be constexpr (or const at least)"
- [!8406](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8406) nicolas.vuaille, 2021-09-14: "I think we prefer uppercase for constexpr variable names"
- [!8182](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8182) ben.boeckel, 2021-08-05: "These should all be declared `static` or `constexpr`, no?"

### R116: Prefer using over typedef for type definitions.

Rationale: Reviewers stated that using is preferred for consistency and because typedef cannot be used in some iterator framework contexts where using is universally applicable.

- Scope: C++ source files
- Support: 4 MRs, 5 threads, 2021-02-22 to 2022-05-31
- Reviewers: alliepiper16 (2), charles.gueunet (2), will.schroeder (1)
- [!9230](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9230) charles.gueunet, 2022-05-31: "prefer `using` over `typedef`"
- [!8755](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8755) will.schroeder, 2021-12-20: "I think it is more coherent with the whole file to keep the typedef."
- [!8052](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8052) charles.gueunet, 2021-07-01: "prefer `using` over `typedef`"

### R117: Remove the `static` keyword from code inside an anonymous namespace and replace `NULL` with `nullptr`.

Rationale: An anonymous namespace is implicitly static, so `static` is redundant and should be removed.

- Scope: all C++ sources
- Support: 4 MRs, 4 threads, 2021-03-12 to 2022-06-14
- Reviewers: ben.boeckel (2), cory.quammen (1), yohann.bearzi (1)
- [!9224](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9224) yohann.bearzi, 2022-06-14: "You should put this code in an anonymous namespace (and remove `static`, which is redundant inside such namespaces)"
- [!7835](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7835) cory.quammen, 2021-04-12: "I suspect clang-tidy will complain about redundancy of `static` in an anonymous namespace. They are both ways to declare something as having internal linkage, so only one or the other is needed (I wou"
- [!7806](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7806) ben.boeckel, 2021-04-06: "namespace /* anon */ { static } is redundant → remove static NULL → nullptr"

### R118: Initialize pointer members to nullptr in the header and avoid explicit nullptr initialization in constructors for vtkSmartPointer members.

Rationale: vtkSmartPointer members are initialized to nullptr by default, so explicit initialization is unnecessary.

- Scope: C++ source files for new VTK classes
- Support: 4 MRs, 4 threads, 2021-06-16 to 2024-12-03
- Reviewers: timothee.chabat (1), utkarsh.ayachit (1), dgobbi (1), jaswant.panchumarti (1)
- [!11567](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11567) jaswant.panchumarti, 2024-12-03: "Please set defaults for integers, and initlaize pointers to `nullptr` in the header rather than doing it in constructor. IIRC, This is how new VTK classes should be written."
- [!9616](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9616) dgobbi, 2022-10-12: "Since `this->LookupTable` is a `vtkSmartPointer`, there is no need to set it to `nullptr` in the `vtPlotBar` constructor."
- [!8391](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8391) utkarsh.ayachit, 2021-09-08: "this is not correct. `OutputGhostArrayName` needs be initialized to nullptr before calling `SetOutputGhostArrayName`. ```c++ vtkExtractGhostCells::vtkExtractGhostCells() : OutputGhostArrayName(nullptr"

### R119: Set the first enum value explicitly and add new enum values at the end to maintain backward compatibility and avoid index changes.

Rationale: To avoid future testing errors and ensure backward compatibility by preserving index correspondence.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2021-09-08 to 2024-06-03
- Reviewers: julien.fausty (2), finetjul (1), lucas.givord (1)
- [!11165](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11165) lucas.givord, 2024-06-03: "we should generally set the first value of an enum (to avoid error in the future for some testing...)"
- [!10197](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10197) julien.fausty, 2023-05-15: "Here and everywhere this ordering would impact: I would argue to not insert `PROCESSIDS` in the middle since this is going to move all the index correspondence and change all the APIs that rely on thi"
- [!9599](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9599) julien.fausty, 2022-10-06: "The presence of this clamp macro is all the more important I think to explicitly set the integer value of your enum. I know that the standard now is to increment enums in the order of their declaratio"

### R120: Use const reference for function parameters to avoid copying.

Rationale: The reviewers stated that using const reference avoids copying of parameters.

- Scope: C++ sources
- Support: 4 MRs, 5 threads, 2021-10-05 to 2024-06-25
- Reviewers: thomas.galland (3), ben.boeckel (1), jaswant.panchumarti (1)
- [!11261](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11261) jaswant.panchumarti, 2024-06-25: "Can this be `const`? No one else modifies the map. It's only passed in the call to `CalculateAngles` which happens to use `const`. ```suggestion:-0+0 const vtkPolyhedron::vtkPointIdMap& pointIdMap) ``"
- [!10322](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10322) thomas.galland, 2023-07-07: "`const std::set<std::string>&` ?"
- [!8650](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8650) thomas.galland, 2021-12-09: "const std::list<int>& valueList"

### R122: Use the std::vector constructor with size and value arguments instead of resize followed by assignment or fill.

Rationale: This avoids unnecessary reallocation and initialization steps.

- Scope: C++ sources
- Support: 4 MRs, 6 threads, 2022-05-12 to 2025-07-24
- Reviewers: mwestphal (3), spiros.tsalikis (1), charles.gueunet (1), leon.victor (1)
- [!11285](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11285) leon.victor, 2024-08-26: "Use https://en.cppreference.com/w/cpp/container/vector/vector (3) ? (here an below)"
- [!10609](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10609) charles.gueunet, 2023-10-24: "std::vector<vtkIdType> outPointIds = { ptId1, ptId2 }; to avoid unneeded reallocation."
- [!9148](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9148) spiros.tsalikis, 2022-05-12: "No need to use fill, do the following. ```c++ std::vector<vtkIdType> pointIdRedirectionMap(numPoints, -1); ```"

### R123: Keep indentation consistent throughout the code.

*Mixed evidence: check the examples before accepting.*

Rationale: Reviewers noted indentation mismatches and inconsistencies that should be avoided.

- Scope: all C++ sources
- Support: 3 MRs, 3 threads, 2017-10-25 to 2024-08-21
- Reviewers: dgobbi (1), mzeyen (1), ben.boeckel (1)
- [!11003](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11003) ben.boeckel, 2024-08-21: "Indentation mismatch (here and elsewhere)"
- [!5335](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5335) mzeyen, 2019-04-17: "Indentation inconsistent with other documentation."
- [!3490](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3490) dgobbi, 2017-10-25: "There's a change in the indentation here. Indentation should be kept consistent."
- Counter-evidence:
  - [!1007](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1007) sankhesh, 2015-12-15: "Style: No need for extra indentation"
  - [!2537](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2537) alouis, 2017-03-09: "Indentation must be two spaces shorter"

### R125: Add a default case to switch statements.

*Mixed evidence: check the examples before accepting.*

Rationale: To handle unexpected values and avoid compiler warnings.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2019-04-16 to 2023-08-07
- Reviewers: mwestphal (1), charles.gueunet (1), julien.fausty (1)
- [!10233](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10233) julien.fausty, 2023-08-07: "`default` to error I would say just in case."
- [!10026](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10026) charles.gueunet, 2023-05-03: "Its ok, having an explicit default is still a good habit, and avoid some warning on older compiler, but ok for me."
- [!5377](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5377) mwestphal, 2019-04-16: "switch case ?"
- Counter-evidence:
  - [!59](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/59) dgobbi, 2015-03-27: "If the behavior is to stay the same, I'd suggest adding an else rather than allowing fall-through:"

### R129: Capitalize the first letter of every attribute name.

*Mixed evidence: check the examples before accepting.*

Rationale: The reviewers stated that attributes should follow a naming convention where the first letter is capitalized.

- Scope: all C++ sources
- Support: 3 MRs, 3 threads, 2018-01-17 to 2020-09-21
- Reviewers: yohann.bearzi (2), mwestphal (1)
- [!7247](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7247) yohann.bearzi, 2020-09-21: "Please add a cap on first letter of every attributes. For instance, replace `pointToIncidentFaces` by `PointToIncidentFaces`."
- [!6295](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6295) yohann.bearzi, 2019-12-12: "Naming convention: first letter should be upper case. Same thing for `addPoints`."
- [!3745](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3745) mwestphal, 2018-01-17: "first leter caps"
- Counter-evidence:
  - [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) michael.migliore, 2020-03-10: "use lower case for the first letter here. You can rename the variable to `reader`"

### R130: Use constexpr for member initializations in constructors and for hard-coded values in performance-critical functions.

*Mixed evidence: check the examples before accepting.*

Rationale: To avoid implicit mutex checks that lock cache lines and improve performance.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2021-03-05 to 2023-03-23
- Reviewers: thomas.caissard (1), thomas.galland (1), mwestphal (1)
- [!9654](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9654) thomas.galland, 2022-11-10: "I think you can use `constexpr double ...` here has the value is hard-coded"
- [!7700](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7700) thomas.caissard, 2021-03-05: "Better not declare it `static` as it implicitly adds a mutex check each time you enter the function (and thus locks the cache line). `constexpr` would be better for that case!"
- [!10078](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10078) mwestphal, 2023-03-23: "constexpr"
- Counter-evidence:
  - [!4114](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4114) ken-martin, 2018-03-23: "constexpr std::size_t size = 5000; ... const std::size_t size = 5000;"

### R140: Add a separator line `//------------------------------------------------------------------------------` above certain code blocks.

*Mixed evidence: check the examples before accepting.*

Rationale: to improve readability of the code.

- Scope: C++ sources
- Support: 3 MRs, 4 threads, 2023-11-07 to 2024-11-07
- Reviewers: lucas.givord (2), mwestphal (2)
- [!11602](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11602) mwestphal, 2024-11-07: "//------------------------------------------------------------------------------ add `//------------------------------------------------------------------------------` above"
- [!10638](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10638) lucas.givord, 2023-11-09: "could you please add for each method this comment for the readability ? `//----------------------------------------------------------------------------` (same for the TestHDFReader.cxx)"
- [!10659](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10659) mwestphal, 2023-11-07: "//------------------------------------------------------------------------------ // add `//------------------------------------------------------------------------------` everywhere needed"
- Counter-evidence:
  - [!9763](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9763) lucas.givord, 2023-03-10: "please use only `//----------` like above"

### R142: Group tests with the vtk_add_text_cxx() call above them and include NO_VALID if there is no valid screenshot image, and ensure test names are consistent with other VTK test names by removing underscores.

Rationale: This ensures test reports are complete and test names are consistent with other VTK test names.

- Scope: tests
- Support: 3 MRs, 3 threads, 2015-09-09 to 2017-11-10
- Reviewers: cory.quammen (1), aashish-chaudhary (1), dgobbi (1)
- [!3494](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3494) dgobbi, 2017-11-10: "This should be grouped with the `vtk_add_text_cxx()` call that occurs above it. Also, it needs `NO_VALID` to tell cmake that there is no valid screenshot image for this test."
- [!3432](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3432) aashish-chaudhary, 2017-10-14: "Yes. It is a CMake/CTest feature which ensures that when the test failure report is compiled, nothing is left out. Most (if not all) VTK tests have this statement."
- [!246](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/246) cory.quammen, 2015-09-09: "Would you mind dropping the underscore from the test name, e.g. TestDelaunay2D_FindTriangle.cxx -> TestDelaunay2DFindTriangle.cxx? This would make the test name more consistent with the other test nam"

### R143: Split lines longer than 80 characters across multiple lines.

Rationale: The reviewers stated that lines should be under 80 characters and can be split.

- Scope: all C++ sources
- Support: 3 MRs, 3 threads, 2015-09-09 to 2017-06-16
- Reviewers: alliepiper16 (2), demarle (1)
- [!2930](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2930) demarle, 2017-06-16: "split long lines <=80 chars please"
- [!1657](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1657) alliepiper16, 2016-07-13: "Line length should be <80 characters"
- [!397](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/397) alliepiper16, 2015-09-09: "Please keep lines under 80 characters. This can be split like: ..."

### R145: Declare loop counters as unsigned int.

Rationale: To avoid signed/unsigned comparison warnings.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2016-05-18 to 2023-02-03
- Reviewers: dgobbi (1), mwestphal (1), timothee.chabat (1)
- [!1502](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1502) dgobbi, 2016-05-18: "for (int i` -> `for (unsigned int i"
- [!9912](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9912) timothee.chabat, 2023-02-03: "vector<unsigned int>"
- [!5377](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5377) mwestphal, 2019-04-16: "`uint32_t`"

### R146: Be consistent with the order of switch cases and use switch case labels without parentheses.

Rationale: Reviewers stated that switch cases should be ordered consistently and that parentheses are unnecessary around case labels.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2016-10-03 to 2023-12-30
- Reviewers: jpouderoux (2), spiros.tsalikis (1)
- [!10769](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10769) spiros.tsalikis, 2023-12-30: "One stylistic comment: Be consistent with the order of switch cases. Previously it was generic, 32, 64/default, here it is 64, 32, generic."
- [!3310](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3310) jpouderoux, 2017-09-27: "don't need parenthesis for cases"
- [!2024](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2024) jpouderoux, 2016-10-03: "no need to put case values between parenthesis"

### R148: There should be a space after the 'for' keyword.

Rationale: The reviewers stated that a space after 'for' improves formatting.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2017-02-17 to 2019-04-23
- Reviewers: mwestphal (1), jpouderoux (1), michael.migliore (1)
- [!4707](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4707) jpouderoux, 2018-09-26: "formatting: please put space after keywords (for, if, while etc)"
- [!5038](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5038) michael.migliore, 2019-04-23: "space after `for`"
- [!2486](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2486) mwestphal, 2017-02-17: "spacing "for (""

### R149: Add spaces for proper spacing throughout the code.

- Scope: all C++ sources
- Support: 3 MRs, 3 threads, 2017-02-17 to 2018-01-16
- Reviewers: mwestphal (2), jpouderoux (1)
- [!3767](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3767) mwestphal, 2018-01-16: "spacing, here and everywhere."
- [!3604](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3604) jpouderoux, 2017-12-12: "add spaces"
- [!2486](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2486) mwestphal, 2017-02-17: "spacing"

### R150: Use 'the source' instead of 'it' in documentation comments and use 'its' instead of 'is' in comments.

Rationale: The reviewers stated that 'it' should be replaced with 'the source' and 'is' should be replaced with 'its' in comments.

- Scope: documentation comments and comments in C++ source files
- Support: 3 MRs, 3 threads, 2017-03-21 to 2023-08-11
- Reviewers: alouis (1), luzpaz (1), tiffany.chhim (1)
- [!10399](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10399) tiffany.chhim, 2023-08-11: ""it" -> "the source""
- [!4086](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4086) luzpaz, 2018-03-20: "The `is` should be `its`: // Whether its representation can handle a selection."
- [!2513](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2513) alouis, 2017-03-21: "in in -> it in"

### R152: Place opening braces on the same line as the control statement.

Rationale: The reviewers stated that the new coding standard requires braces to be in line with the if/else statement and suggested this style for range-based for loops.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2017-05-05 to 2025-09-05
- Reviewers: ken-martin (1), dgobbi (1), mwestphal (1)
- [!2772](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2772) ken-martin, 2017-05-05: "You may not be aware but we changed the coding style for VTK a couple months ago. The new standard requires braces to be in line with the if/else statement"
- [!12430](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12430) mwestphal, 2025-09-05: suggested `for (const auto& [id, coords] : expectedValues) {`
- [!11506](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11506) dgobbi, 2024-09-23: "Braces, `this`."

### R156: Use clang-format to format code according to VTK's specification.

Rationale: The contribution workflow includes conformity checks that require code to conform to the clang-format specification.

- Scope: all C++ sources
- Support: 3 MRs, 3 threads, 2018-01-11 to 2023-04-19
- Reviewers: mwestphal (1), sebastien.jourdain (1), halowine (1)
- [!10109](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10109) halowine, 2023-04-19: "It is part of the contribution workflow dedicated to running conformity checks. In this instance it looks like it failed due to the formatting of the changes which were not conform to the `clang-forma"
- [!5271](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5271) sebastien.jourdain, 2019-03-05: "You may want to use clang-format with the ParaView config file."
- [!3767](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3767) mwestphal, 2018-01-11: "spacing in all this file. I would recommend using clang-format -i"

### R162: Sort items alphabetically

- Scope: all C++ sources
- Support: 3 MRs, 3 threads, 2018-11-26 to 2024-01-23
- Reviewers: michael.migliore (1), louis.gombert (1), charles.gueunet (1)
- [!10833](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10833) charles.gueunet, 2024-01-23: "alphabetic order"
- [!10732](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10732) louis.gombert, 2023-11-30: "Sort alphabetically"
- [!4909](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4909) michael.migliore, 2018-11-26: "alphabetical order"

### R164: Use braces in code.

Rationale: The reviewers stated that braces are required or part of style.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2019-04-09 to 2023-03-15
- Reviewers: ken-martin (1), cory.quammen (1), LucasGandelKitware (1)
- [!10026](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10026) LucasGandelKitware, 2023-03-15: "use braces"
- [!7806](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7806) cory.quammen, 2021-04-02: "Need curly braces."
- [!5380](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5380) ken-martin, 2019-04-09: "Style braces"

### R165: Use std::clamp, std::max, and std::min directly instead of manual if-checks, ternary operators, or custom macros for clamping values.

Rationale: The reviewers stated that std::clamp or std::max/min should be used directly for clamping values.

- Scope: C++ sources
- Support: 3 MRs, 4 threads, 2019-06-21 to 2025-12-10
- Reviewers: mwestphal (2), lorensen (1), spiros.tsalikis (1)
- [!12321](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12321) spiros.tsalikis, 2025-12-10: "would std::clamp be useful here? Yes. Done."
- [!5527](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5527) lorensen, 2019-06-21: "Why are these #define's needed? use std::min and std::max directly."
- [!12611](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12611) mwestphal, 2025-11-18: "std::max ?"

### R167: Each header file must include only what it uses and provide a comment explaining why each include is needed.

Rationale: The reviewers stated that HeaderTest fails without comments justifying includes, and extra includes must be justified or excluded.

- Scope: C++ header files
- Support: 3 MRs, 3 threads, 2019-11-25 to 2025-12-30
- Reviewers: demarle (1), mwestphal (1), sankhesh (1)
- [!12747](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12747) sankhesh, 2025-12-30: "Without that comment, the HeaderTest is failing on this MR."
- [!11602](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11602) mwestphal, 2024-11-14: "each header include should have a comment explaining why its needed eg: #include "vtkSmartPointer.h" // for smart pointer"
- [!6231](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6231) demarle, 2019-11-25: "One of the regression tests checks vtk code guidelines such as does a public header file have only one include in it. Two workarounds for that are to 1) add a comment to justify the extra includes, 2)"

### R169: Name variables to reflect their purpose and direction of iteration.

Rationale: The reviewers stated that variable names should reflect purpose and direction of iteration.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2020-03-06 to 2023-12-22
- Reviewers: michael.migliore (1), timothee.chabat (1), jcfr (1)
- [!10783](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10783) jcfr, 2023-12-22: "Why is the ivar called `oldcam` ? Should it be `activecam` instead ?"
- [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) michael.migliore, 2020-03-06: "I renamed nbLines into nbLinesLeft"
- [!9170](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9170) timothee.chabat, 2022-05-10: "i -> axis"

### R170: Prefix all standard library types with std::.

- Scope: all C++ sources
- Support: 3 MRs, 3 threads, 2020-03-10 to 2025-12-09
- Reviewers: michael.migliore (1), charles.gueunet (1), lucas.givord (1)
- [!12699](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12699) lucas.givord, 2025-12-09: "maybe it's time for some clean in this code, every `size_t` should be prefixed by his namespace so `std::size_t`"
- [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) michael.migliore, 2020-03-10: "add `std::` before all `istream` occurrences"
- [!9471](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9471) charles.gueunet, 2022-08-18: "same, `std::`"

### R171: Make internals private unless inheritance is intended.

Rationale: To prevent unintended inheritance and for deprecation purposes.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2020-03-10 to 2024-12-03
- Reviewers: jpouderoux (1), thomas.galland (1), jaswant.panchumarti (1)
- [!11567](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11567) jaswant.panchumarti, 2024-12-03: "Please make internals `private`. ```suggestion:-1+0 class vtkInternals; std::unique_ptr<vtkInternals> Internals. ```"
- [!10587](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10587) thomas.galland, 2023-10-13: "I think you can move all the internal methods to `private`, since you're class is not (at least for now) intended to be inherited from, and for deprecation purposes"
- [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) jpouderoux, 2020-03-10: "I would put all the following methods as protected instead (this is usually done like this in VTK)"

### R172: Define variables as close as possible to where they are used, using one variable declaration per line and lowercase names.

Rationale: This follows VTK style conventions.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2020-04-06 to 2022-04-26
- Reviewers: yohann.bearzi (1), finetjul (1), cory.quammen (1)
- [!9087](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9087) cory.quammen, 2022-04-26: "For modern VTK we really should be in the habit of defining variables as close to where they are used as possible."
- [!7504](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7504) finetjul, 2021-01-08: "vtk style requires 1 variable declaration per line."
- [!6686](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6686) yohann.bearzi, 2020-04-06: "In this entire section, local variables should be on lower case to respect VTK style, i.e. `Id` becomes `id`, etc."

### R176: Use emplace instead of insert with a pair or make_pair, and use brace initialization for map insertions.

Rationale: These changes remove the need for explicit make_pair or std::make_pair constructions.

- Scope: C++ sources
- Support: 3 MRs, 4 threads, 2020-09-18 to 2022-06-15
- Reviewers: charles.gueunet (3), ben.boeckel (1)
- [!9230](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9230) charles.gueunet, 2022-06-15: "emplace_back should remove the need for the explicit make_pair"
- [!7262](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7262) ben.boeckel, 2020-09-18: "vtkWindowHandleToDeviceObjectConnection.insert({ this->WindowHandle, this });"
- [!9042](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9042) charles.gueunet, 2022-04-05: suggested `if (this->TimeStepIndices.emplace(timeStepIndex).second)`

### R177: Use #if instead of #ifdef for preprocessor directives.

Rationale: The reviewers stated that #if is preferred because the define is always defined.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2020-09-18 to 2022-04-08
- Reviewers: ben.boeckel (1), dgobbi (1), cory.quammen (1)
- [!9052](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9052) cory.quammen, 2022-04-08: "I could be wrong, and I forget why, but I think the preferred form in VTK is `#if defined(_WIN32)`"
- [!8162](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8162) dgobbi, 2021-07-23: "Also, it might be worth keeping two separate #if directives for 64BIT_FLOOR. Originally I split ia64 checks apart from the others to keep the #if line length below 80 chars. If the line is over-long, "
- [!7262](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7262) ben.boeckel, 2020-09-18: "This makes a define called `VTK_MODULE_ENABLE_VTK_RenderingTDx` available that you can use in the code. Use `#if` because it is always defined."

### R181: Factorize repeated code into a single function.

Rationale: The reviewers stated that repeated code should be consolidated into one function to avoid duplication.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2021-09-01 to 2023-12-07
- Reviewers: LucasGandelKitware (1), mwestphal (1), lucas.givord (1)
- [!10744](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10744) lucas.givord, 2023-12-07: "could be factorize with the previous one"
- [!10459](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10459) mwestphal, 2023-08-31: "you can work with a dataobject and factorize these two"
- [!8303](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8303) LucasGandelKitware, 2021-09-01: "Can you factorize this in one function and have this->TranslateAxis(...) the same way it is done for this->RotateAxis..."

### R182: Use the VTK_FALLTHROUGH macro for intentional fallthrough in switch statements when the case contains actual code.

Rationale: It serves as the VTK equivalent of the C++11 fallthrough attribute to indicate intentional fallthrough.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2022-01-12 to 2022-12-16
- Reviewers: mwestphal (2), scott.wittenburg (1)
- [!9757](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9757) scott.wittenburg, 2022-12-16: "this is the VTK equivalent, C++11 compatible of https://en.cppreference.com/w/cpp/language/attributes/fallthrough"
- [!9398](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9398) mwestphal, 2022-08-11: "you need VTK_FALLTHROUGH only when your case contains actual code."
- [!8804](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8804) mwestphal, 2022-01-12: "VTK_FALLTHROUGH"

### R184: Document that epsilon is the minimum difference divided by 10 and ensure it is at least as large as the tolerance using std::max.

Rationale: Having epsilon smaller than the tolerance was considered a bad idea, so epsilon should be defined as the minimum difference divided by 10 and ensured to be at least as large as the tolerance using std::max.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2022-05-31 to 2023-12-14
- Reviewers: charles.gueunet (1), julien.fausty (1), mwestphal (1)
- [!10750](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10750) mwestphal, 2023-12-14: "document that epsilon is the min difference divided by 10"
- [!9456](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9456) julien.fausty, 2022-08-03: "actually having epsilon < tolerance was a really bad idea. `std::max(epsilon, tol * 2.0)` seems indeed like a better idea"
- [!9230](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9230) charles.gueunet, 2022-05-31: "may we define this epsilon once and for all at the beginning of the file ?"

### R185: Use brace initialization for arrays.

Rationale: The reviewers stated that brace initialization is preferred for array initialization, as it avoids the need for std::fill.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2022-05-31 to 2023-08-10
- Reviewers: julien.fausty (2), charles.gueunet (1)
- [!9812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9812) julien.fausty, 2023-05-05: "-0+0 double deriv[3] = { 0.0 }; double values[8] = { 0.0 };"
- [!9230](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9230) charles.gueunet, 2022-05-31: "using: ```suggestion:-0+0 std::array<unsigned int, 3> bin{}, ``` you won't need the `std::fill` below"
- [!10233](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10233) julien.fausty, 2023-08-10: suggested `double xyz[3] = { 0.0, 0.0, 0.0 };`

### R186: Avoid using first person pronouns such as I, we, you, or your in comments and code

Rationale: Reviewers stated that using first person or personal judgement is discouraged

- Scope: all C++ sources
- Support: 3 MRs, 3 threads, 2022-06-06 to 2024-03-11
- Reviewers: mwestphal (1), tiffany.chhim (1), louis.gombert (1)
- [!10951](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10951) louis.gombert, 2024-03-11: "Don't use first person or personal judgement"
- [!9468](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9468) tiffany.chhim, 2022-09-19: "I think we should avoid using words such as "you", or "your", so: `if the input`"
- [!9230](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9230) mwestphal, 2022-06-06: "Avoid I and We in comments"

### R187: Use the do-while(0) pattern for macros to avoid semicolon issues and enable usage in conditions without braces.

Rationale: To avoid bad semicolon behavior with C macros and allow the macro to be used in conditions without braces.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2022-06-28 to 2023-07-21
- Reviewers: mwestphal (1), ben.boeckel (1), lucas.givord (1)
- [!10330](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10330) lucas.givord, 2023-07-21: "as it's to avoid bad semicolon behavior with c macro, you can do your `do while(false)` at the end of the macro right? This also handle potential problems with conditions: https://gcc.gnu.org/onlinedo"
- [!10081](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10081) ben.boeckel, 2023-03-27: "Please use the `do { } while (0)` trick as this fails when used in a condition without braces: ``` if (some_cond) Check(expr, msg); ```"
- [!9330](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9330) mwestphal, 2022-06-28: "To allow a semicolon to be used at the usage site."

### R193: Put all class members as private and provide accessors for deprecation.

Rationale: It enables proper deprecation and future refactoring.

- Scope: C++ class members
- Support: 3 MRs, 3 threads, 2024-03-28 to 2025-04-01
- Reviewers: mwestphal (1), thomas.galland (1), nicolas.vuaille (1)
- [!11209](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11209) nicolas.vuaille, 2025-04-01: "Last, I advise to put all class members as private instead of protected: this helps a lot with deprecation and future refactor!"
- [!10852](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10852) mwestphal, 2024-05-28: "There is no proper way to deprecate a protected member. Using an accessor is the only way to be able to do it."
- [!10995](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10995) thomas.galland, 2024-03-28: "I think we can consider setting it `private` and accessed through getters in subclasses (better for potential future depreciation IMO)"

## process-ci

### R001: Squash all commits into logical or a single commit before merging.

Rationale: Reviewers stated that squashing makes the commit history clearer and prepares the change for merging.

- Scope: all commits
- Support: 38 MRs, 40 threads, 2015-03-31 to 2023-03-22
- Reviewers: mwestphal (16), jpouderoux (5), utkarsh.ayachit (4), dgobbi (3), michael.migliore (3)
- [!7521](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7521) mwestphal, 2023-03-22: "Great, please squash your two commits into one and force push."
- [!8648](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8648) mwestphal, 2022-02-03: "please squash your commits logcically"
- [!7219](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7219) mwestphal, 2022-02-02: "please squash your commits into one"

### R008: Rebase on master and run CI again after fixing any issues.

*Mixed evidence: check the examples before accepting.*

Rationale: The reviewers require a rebased branch with green CI to ensure the build is working correctly.

- Scope: all code changes
- Support: 20 MRs, 20 threads, 2016-05-15 to 2024-08-08
- Reviewers: mwestphal (9), cory.quammen (6), LucasGandelKitware (1), williamfgc (1), rupertnash (1)
- [!11319](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11319) mwestphal, 2024-08-08: "please rebase on master and force push"
- [!11085](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11085) mwestphal, 2024-05-14: "please rebase on master, force push, reformat and run CI."
- [!9776](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9776) mwestphal, 2023-03-17: "Please rebase on master to get CI working."
- Counter-evidence:
  - [!479](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/479) ben.boeckel, 2015-08-04: "Please rebase onto release: ```sh git rebase --onto origin/release origin/master FixDegeneratedPolygonCrash ```"
  - [!12121](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12121) berkgeveci, 2025-05-16: "Rebase onto current release. Create MR targeting master."

### R027: Use `git cherry-pick -x` to record the original commit SHA in the commit message when cherry-picking.

Rationale: The reviewers stated that using `-x` records the original commit SHA in the commit message for easy tracking and to preserve commit history.

- Scope: C++ sources
- Support: 9 MRs, 10 threads, 2016-02-03 to 2024-01-30
- Reviewers: cory.quammen (3), ben.boeckel (2), utkarsh.ayachit (2), lucas.givord (2), seanm (1)
- [!10846](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10846) lucas.givord, 2024-01-30: "could you please use `cherry-pick -x` ?"
- [!10847](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10847) lucas.givord, 2024-01-30: "could you please use `cherry-pick -x` (we can track the original commit with this option) ?"
- [!9609](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9609) cory.quammen, 2022-10-07: "I should have asked you to use the option `-x` (e.g., `git cherry-pick -x`) to record the original commit SHA that was backported."

### R031: Create a merge request based on the release branch and add "Backport: release" as the last line in the description.

*Mixed evidence: check the examples before accepting.*

Rationale: The robot uses this to automatically backport changes to the release branch.

- Scope: gitlab MR descriptions
- Support: 8 MRs, 10 threads, 2019-01-24 to 2025-05-21
- Reviewers: dgobbi (2), ben.boeckel (1), dcthomp (1), ppebay (1), michael.migliore (1)
- [!12121](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12121) berkgeveci, 2025-05-21: "the backport trailer in the description tells the robot to do that"
- [!10471](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10471) mwestphal, 2023-09-04: "please rebase on the `release` branch and add `Backport: release` in the MR descr"
- [!9674](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9674) dgobbi, 2023-01-04: "Please edit the description text to add `Backport: release` so that the bot will backport to the release branch when it's merged."
- Counter-evidence:
  - [!7644](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7644) cory.quammen, 2021-02-19: "Please target this MR to `master`. Backporting can be done in another MR targeting `paraview/release` with changes appropriate for that branch."
  - [!8846](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8846) seanm, 2022-01-31: "the MR 'main target' (what gitlab knows about) should be 'the newest branch' (here, `master`)"
  - [!9371](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9371) charles.gueunet, 2022-07-11: "You would need to rebase you change to `release^` (last commit before the branching). You would also need to add `Release: backport` at the end of the description of your MR."

### R045: Merge into paraview/release, not master, and ensure the description ends with Backport: paraview/release.

*Mixed evidence: check the examples before accepting.*

Rationale: The reviewers stated that merging into paraview/release ensures the change gets into ParaView and that the description must end with Backport: paraview/release.

- Scope: all C++ sources
- Support: 7 MRs, 7 threads, 2020-05-11 to 2023-03-29
- Reviewers: cory.quammen (5), boonth (1), caitlin.ross (1)
- [!10100](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10100) caitlin.ross, 2023-03-29: "Oh wait, need to merge into paraview/release, not master."
- [!9666](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9666) cory.quammen, 2022-11-02: "The target branch needs to be `paraview/release` to get into ParaView."
- [!8938](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8938) boonth, 2022-02-28: "Did you base this branch off of the `paraview/release` branch? If so, add `Backport: paraview/release` to the end of your merge request description."
- Counter-evidence:
  - [!11237](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11237) mwestphal, 2024-06-17: "Lets not bacckport anything for now, please merge in master only or wait for ParaView release process to complete: https://discourse.vtk.org/t/please-do-not-backport-to-release-or-paraview-release-bra"
  - [!11460](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11460) cory.quammen, 2024-09-06: "API changes should definitely not go in `paraview/release`, let me check the list. Indeed, https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11317 is not a bug fix, should not be backported. https:/"
  - [!11485](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11485) mwestphal, 2024-09-18: "you need either a bypass token or rebase on lastet paraview/release"

### R051: Rebase your topic branch onto master and avoid merge commits before pushing.

*Mixed evidence: check the examples before accepting.*

Rationale: To keep the topic branch clean and consist only of your commits.

- Scope: topic branches
- Support: 6 MRs, 6 threads, 2018-01-02 to 2025-07-10
- Reviewers: dgobbi (2), alliepiper16 (1), fdepourcq (1), cory.quammen (1), akaszynski (1)
- [!12273](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12273) dgobbi, 2025-07-10: "we generally do not accept MRs that contain merge commits. Commits from master must be brought into the topic branch by rebasing the branch on master, rather than by merging master into the branch."
- [!8092](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8092) akaszynski, 2021-06-22: "FWIW, we prefer to rebase so that the topic is just your commits instead of also bringing in changes from `master`."
- [!7375](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7375) cory.quammen, 2020-11-05: "Please remove the merge from `master`. Instead, rebase this branch on `master`."
- Counter-evidence:
  - [!5337](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5337) ben.boeckel, 2019-03-28: "When we merge that will put it into both branches. I'll do it here, but the other MRs should do the same if they also should go into `master`."
  - [!11997](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11997) sankhesh, 2025-03-21: "you shouldn't be making a merge request against the release branch. Please fix your fork based on Cory's comments above Rebase these changes onto the release branch Change the target of the merge requ"

### R062: Add a comment containing the exact text "Do: merge" to trigger the merge process.

Rationale: The reviewers stated that the merge command is "Do: merge" and that adding this comment signals the system to merge the branch.

- Scope: all code changes requiring a merge (i.e., all branches)
- Support: 6 MRs, 6 threads, 2017-12-21 to 2021-01-04
- Reviewers: cory.quammen (2), dcthomp (1), acbauer (1), sebastien.jourdain (1), ken-martin (1)
- [!7491](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7491) cory.quammen, 2021-01-04: "the merge command is `Do: merge`. We usually leave it to the MR author to merge in case you decide more changes are needed or want to withdraw the merge request."
- [!6565](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6565) cory.quammen, 2020-03-19: "Actually, will defer the merge to you @boonth. To merge, just write a comment with `Do: merge` on the last line (not sure if you've merged before, but you should have permission)."
- [!5539](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5539) ken-martin, 2019-05-23: "You can merge by adding a comment with "Do: merge" in it"

### R067: Add a `Reviewed-by: @user` line after pushing new commits and before merging, and include an `Acked-by: @user` line in the merge comment if rebasing or squashing.

Rationale: Reviewers require explicit credit to reviewers in the merge comment to ensure their review is recorded in the git history.

- Scope: All code repositories using merge comments after pushes, including rebase/squash workflows.
- Support: 6 MRs, 6 threads, 2019-09-26 to 2023-09-12
- Reviewers: cory.quammen (2), mwestphal (2), spiros.tsalikis (1), louis.gombert (1)
- [!10490](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10490) louis.gombert, 2023-09-12: "you need to have new line between each reviewed-by and do merge"
- [!10488](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10488) mwestphal, 2023-09-11: "As documented in the guide, please use the `Reviewed-by` syntax when merging after a push without a reconfirmation of the reviewer."
- [!10463](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10463) mwestphal, 2023-09-04: "use the Reviewed-by/Acked-by syntax when merging after a push, as documented in the guide"

### R072: Use `Do: test -s quick` before running the full `Do: test` pipeline to conserve CI resources and reduce testing load.

Rationale: To conserve CI resources and reduce testing load on the CI system.

- Scope: all C++ sources
- Support: 6 MRs, 6 threads, 2024-06-07 to 2025-12-10
- Reviewers: mwestphal (4), cory.quammen (2)
- [!12664](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12664) mwestphal, 2025-12-10: "Please avoid running full CI until quick (build) ci is green."
- [!11555](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11555) mwestphal, 2024-10-31: "Please avoid running all tests unless quick tests are successful"
- [!11514](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11514) cory.quammen, 2024-09-24: "Please use `Do: test -s quick` for some quick initial checking of a merge request across fundmental operating systems and configurations. Once it looks like the review process is nearing approval, the"

### R077: Do not merge until CI is clean and the backport is ready.

*Mixed evidence: check the examples before accepting.*

Rationale: Reviewers stated that merging without checking CI or having the backport ready is not allowed.

- Scope: all C++ sources
- Support: 5 MRs, 5 threads, 2022-05-21 to 2025-12-19
- Reviewers: mwestphal (3), spiros.tsalikis (1), seanm (1)
- [!12734](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12734) mwestphal, 2025-12-19: "once if have a green CI, you can merge whenever you want once the backport is ready."
- [!10991](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10991) mwestphal, 2024-03-26: "Please avoid merging without checking the CI."
- [!10242](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10242) seanm, 2023-05-30: "As stated in the dev guide, CI run is required before any merge."
- Counter-evidence:
  - [!10850](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10850) thomas.galland, 2024-02-19: "I will give you a +2 (see https://docs.vtk.org/en/latest/developers_guide/git/develop.html#leading-line) and you will be able to merge."

### R079: Cherry-pick the required commits onto the release branch and resolve any conflicts before merging them into the release branch.

Rationale: The reviewers require cherry-picking changes onto the release branch and resolving conflicts before the changes are merged into the release branch.

- Scope: release branch
- Support: 5 MRs, 5 threads, 2016-06-29 to 2019-08-01
- Reviewers: sankhesh (2), utkarsh.ayachit (1), chuck.atkins (1), cory.quammen (1)
- [!5812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5812) cory.quammen, 2019-08-01: "Then, when you create your MR, change the target branch from `vtk/vtk` `master` to `vtk/vtk` `paraview/release`."
- [!2918](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2918) sankhesh, 2017-06-16: "Please rebase / cherry-pick changes onto the release branch and create a merge request to get these changes into 8.0."
- [!2925](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2925) sankhesh, 2017-06-16: "Please rebase / cherry-pick changes onto the release branch and create a merge request to get these changes into 8.0."

### R099: Push to a dedicated branch on your fork instead of pushing to your master branch.

Rationale: This ensures reliable test results and avoids direct commits to master.

- Scope: all code changes requiring a merge request
- Support: 4 MRs, 4 threads, 2017-07-12 to 2024-01-19
- Reviewers: cory.quammen (1), demarle (1), dgobbi (1), mwestphal (1)
- [!10831](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10831) mwestphal, 2024-01-19: "Please push to a dedicated branch on your fork instead of pushing to your master."
- [!5876](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5876) dgobbi, 2019-08-19: "Can you put the fix in a topic branch, instead of the master branch? This will require creating a new merge request, unfortunately."
- [!3228](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3228) demarle, 2017-09-04: "Michal you should checkout -b some-other-topic-name (or similar) instead of working directly off of your master branch with VTK."

### R101: Separate refactoring commits from feature commits and split unrelated changes into separate merge requests.

Rationale: It makes review easier and allows the requester to address requested changes more efficiently.

- Scope: all code changes in merge requests
- Support: 4 MRs, 4 threads, 2017-09-18 to 2023-01-06
- Reviewers: cory.quammen (2), ben.boeckel (1), timothee.chabat (1)
- [!9821](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9821) timothee.chabat, 2023-01-06: "just a quick note for future MRs : I know sometimes it is a bit annoying but it's easier for reviewers if "refactoring" commits and "feature" commits are seperated, especially when there is -1000 +100"
- [!9678](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9678) cory.quammen, 2022-11-10: "the last two commits do not appear to be related to the main topic here. Could you split those into a separate MR?"
- [!8276](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8276) ben.boeckel, 2021-08-08: "I'd also ask about splitting up the commits instead of it being a massive 'fix everything' commit, but that will probably take as long, if not longer, than the changes did themselves."

### R136: Rebase MR branches on master and test them with --merged before merging.

Rationale: Testing the branch as it would be merged avoids failures from outdated code and keeps build times manageable.

- Scope: all MRs
- Support: 3 MRs, 3 threads, 2020-05-20 to 2025-12-16
- Reviewers: utkarsh.ayachit (1), seanm (1), mwestphal (1)
- [!12699](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12699) mwestphal, 2025-12-16: "Usual MR that was not rebased on a change in master. Keep in mind we test the branch, not the branch as if it was merged."
- [!10389](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10389) seanm, 2023-08-03: "Testing is required on every mr before the merge."
- [!6908](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6908) utkarsh.ayachit, 2020-05-20: "When testing MRs, our dashboards do incremental builds by default (unless `Do: test --clean` is specified) to keep the build times down. When testing such branches that are not off a fairly new `maste"

### R153: Use 'addresses #ParaviewIssueNumber' in VTK MR commit messages to link ParaView issues without automatically closing them.

Rationale: Because merging a commit that closes the ParaView issue would prematurely close the issue before ParaView's VTK is updated to fix it.

- Scope: VTK MR commit messages
- Support: 3 MRs, 3 threads, 2017-05-05 to 2025-08-06
- Reviewers: utkarsh.ayachit (2), jaswant.panchumarti (1)
- [!12343](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12343) jaswant.panchumarti, 2025-08-06: "When fixing ParaView issues in VTK, please use "address #ParaviewIssueNumber" or similar in the VTK MR commit message/description to mention that it is related to the ParaView issue. That is sufficien"
- [!8994](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8994) utkarsh.ayachit, 2022-03-15: "when creating VTK mr's, always use `addresses #<paraview issue>` rather than `closes ..` or `fixes ...`. Otherwise gitlab ends up closing the ParaVIew issue as soon as this is merged in VTK. That is n"
- [!2780](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2780) utkarsh.ayachit, 2017-05-05: "I often use `addresses paraview/...` text on commit messages for VTK commits that fix ParaView issues. That way, merging the commit won't automatically close the ParaView issue, since we still need to"

### R160: Check the dashboard before merging and verify it the next day for warnings or errors on all platforms.

Rationale: To prevent warnings or errors on additional platforms from causing issues for other developers.

- Scope: all C++ sources
- Support: 3 MRs, 3 threads, 2018-09-14 to 2022-05-21
- Reviewers: demarle (1), will.schroeder (1), mwestphal (1)
- [!8957](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8957) mwestphal, 2022-05-21: "https://open.cdash.org/viewBuildError.php?type=1&buildid=7925491 C:\glr\builds\vtk\vtk-ci\Filters\Core\vtkPointDataToCellData.cxx(368): warning C4101: 'cellId': unreferenced local variable C:\glr\buil"
- [!5102](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5102) will.schroeder, 2019-01-30: "Whoever does it, make sure that you check the dashboard the next day after the merge. Despite all of the MR testing it is quite common for the additional platforms and associated tests to show up erro"
- [!4635](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4635) demarle, 2018-09-14: "do not merge any change without getting a plus one comment from a reviewer and check the dashboards the day after you merge to see if the wider set of nightly machines turned up anything that needs to"

### R188: Backport fixes to the release branch for the next patch release, and rebase on release to include the changes in the upcoming minor release.

Rationale: The reviewers stated that fixes should be backported to the release branch for a potential patch release and that rebasing on release is required to get the changes into the next minor release.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2022-08-09 to 2025-08-18
- Reviewers: mwestphal (2), dgobbi (1)
- [!10752](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10752) dgobbi, 2025-08-18: "LGTM, but needs "Backport: release" if the intent is to get it into 9.5.1"
- [!10819](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10819) mwestphal, 2024-01-11: "9.3.0 is out already, but fixes should be backported to release for a potential 9.3.1"
- [!9467](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9467) mwestphal, 2022-08-09: "you need to rebase on release to be able to get this in 9.2"

### R190: Only builds must pass before merging; tests may fail.

Rationale: The VTK community has decided that builds must pass, not tests.

- Scope: all C++ sources
- Support: 3 MRs, 3 threads, 2023-01-16 to 2025-05-08
- Reviewers: cory.quammen (1), seanm (1), scott.wittenburg (1)
- [!11938](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11938) scott.wittenburg, 2025-05-08: "There is no requirement for all tests to pass to merge in VTK. Builds must pass, but not tests."
- [!11085](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11085) seanm, 2024-06-03: "Only builds are required to pass prior to merging. You can merge with a failing test."
- [!9805](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9805) cory.quammen, 2023-01-16: "Since the VTK community has decided all builds must pass before merging, we will run into this situation from time to time."

### R192: Prefer using `Do: test` to trigger CI.

Rationale: To check that everything is fine.

- Scope: all C++ sources
- Support: 3 MRs, 3 threads, 2024-02-16 to 2025-06-13
- Reviewers: thomas.galland (1), jaswant.panchumarti (1), mwestphal (1)
- [!12208](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12208) mwestphal, 2025-06-13: "and finally, please prefer using `Do: test` to trigger CI :)"
- [!10924](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10924) jaswant.panchumarti, 2024-02-28: "You can run the CI by commenting `Do: test` without the backticks."
- [!10850](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10850) thomas.galland, 2024-02-16: "Please also run the CI when it's done by using the `Do: test` command, to check everything is fine"

## memory-ownership

### R004: Use vtkNew for VTK object creation to avoid manual memory management and ensure proper reference counting.

*Mixed evidence: check the examples before accepting.*

Rationale: Reviewers stated that vtkNew avoids manual ->Delete() and nullptr handling and prevents memory leaks by ensuring proper reference counting.

- Scope: C++ sources
- Support: 25 MRs, 37 threads, 2015-08-21 to 2021-03-22
- Reviewers: mwestphal (8), utkarsh.ayachit (8), jpouderoux (5), michael.migliore (4), mhanwell (3)
- [!6016](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6016) utkarsh.ayachit, 2019-10-09: "this, I suspect is the leak. Note type of `auto outputMBDS` is `vtkMultiBlockDataSet` and not `vtkSmartPointer<vtkMultiBlockDataSet>`. I'd change it to not be `auto` instead be `vtkSmartPointer<vtkMul"
- [!5439](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5439) jpouderoux, 2019-04-18: "vtkNew would be shorter here"
- [!5261](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5261) amaclean, 2019-03-04: "Personally I would prefer `vtkNew`, in this case, as it makes the code neater and easier to read."
- Counter-evidence:
  - [!4696](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4696) danlipsa, 2018-09-26: "Do you delete this somewhere?"
  - [!4707](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4707) jpouderoux, 2018-09-26: "again, avoid vtknew and PassData"

### R036: Use smart pointers for memory management and member variables.

*Mixed evidence: check the examples before accepting.*

Rationale: Smart pointers prevent deep copying and automatically manage memory.

- Scope: C++ sources
- Support: 8 MRs, 8 threads, 2017-06-09 to 2025-03-27
- Reviewers: mwestphal (3), jpouderoux (2), julien.fausty (1), lucas.givord (1), charly.bollinger (1)
- [!11986](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11986) mwestphal, 2025-03-27: "you should be able to swap without deepcopying anything. If you keep smart pointers to the arrays, they should not be deallocated when calling SetCoord"
- [!10310](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10310) lucas.givord, 2023-07-03: "could be a smart ptr"
- [!9710](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9710) julien.fausty, 2022-12-02: "smart pointer here would be better"
- Counter-evidence:
  - [!5439](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5439) jpouderoux, 2019-04-18: "smartpointers are useless here"
  - [!10197](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10197) julien.fausty, 2023-05-22: "IMO this should be a weak pointer and not a smart pointer"

### R038: Prefer using std::vector over raw arrays for Initialize calls and variable declarations to avoid manual memory management.

Rationale: Using std::vector avoids manual memory management and potential leaks.

- Scope: C++ sources
- Support: 8 MRs, 8 threads, 2016-04-03 to 2025-07-10
- Reviewers: louis.gombert (2), acbauer (1), jpouderoux (1), michael.migliore (1), cory.quammen (1)
- [!11001](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11001) louis.gombert, 2024-03-28: "use std::vector/std::array ? same for facePoints where it can simplify init yes, much better"
- [!10609](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10609) charles.gueunet, 2023-10-23: "you should be able to build this vector with `std::begin(cellOrigin)` and `std::end(cellOrigin)` to avoid the `memcpy` (here and below)"
- [!9912](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9912) timothee.chabat, 2023-02-13: "`std::vector<double[3]>` or `std::vector<std::array<double, 3>>`, but not a vector of heap-allocated doubles that you need to delete`"

### R040: Use smart pointers to avoid explicit manual deletes.

Rationale: The reviewers stated that manual deletes are unnecessary when smart pointers are used.

- Scope: C++ sources
- Support: 8 MRs, 9 threads, 2016-12-06 to 2025-05-20
- Reviewers: mwestphal (2), michael.migliore (2), charles.gueunet (2), jpouderoux (1), will.schroeder (1)
- [!12132](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12132) louis.gombert, 2025-05-20: "you should not need to delete a smart pointer manually. Use TakeSmartPointer or equivalent"
- [!10552](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10552) charles.gueunet, 2023-10-02: "`unique_ptr` ? We need to avoid explicit call to `->delete` at the end."
- [!9346](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9346) mwestphal, 2022-07-08: "If this is not in the destructor it generates a leak, the Controller is not a `vtkSmartPointer` here"

### R047: Use vtkCxxSetObjectMacro for VTK object pointers to ensure proper reference counting and avoid memory leaks.

*Mixed evidence: check the examples before accepting.*

Rationale: It ensures the object is properly freed and prevents dangling pointers or memory leaks.

- Scope: C++ source files
- Support: 7 MRs, 7 threads, 2016-11-03 to 2025-01-15
- Reviewers: mwestphal (4), aashish-chaudhary (1), dgobbi (1), jpouderoux (1)
- [!11842](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11842) mwestphal, 2025-01-15: "it is, otherwise the controller instance is not freed and it creates memory leaks"
- [!11713](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11713) mwestphal, 2024-12-03: "this cannot be nullptr as its a vtkNew"
- [!8618](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8618) mwestphal, 2021-11-18: "use vtkCxxSetObjectMacro in implementation instead."
- Counter-evidence:
  - [!12428](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12428) mwestphal, 2025-09-08: "you can use macros for all of these, see vtkCxxSetSmartPointerMacro"

### R053: Avoid raw pointers if possible, but you can safely use a raw pointer in this case and we usually store raw pointers instead of smart pointers.

*Mixed evidence: check the examples before accepting.*

Rationale: The reviewers stated that using raw pointers is acceptable in certain cases and that they typically store raw pointers instead of smart pointers to avoid unintended changes and memory leaks.

- Scope: C++ sources
- Support: 6 MRs, 6 threads, 2018-05-31 to 2025-10-22
- Reviewers: lucas.givord (2), LucasGandelKitware (1), lassoan (1), michael.migliore (1), scott.wittenburg (1)
- [!12311](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12311) lucas.givord, 2025-10-22: "avoid raw pointer if it's possible"
- [!10022](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10022) lucas.givord, 2023-03-06: "avoid raw pointer if possible"
- [!9873](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9873) scott.wittenburg, 2023-01-24: "Yes, I always try to stop myself from "improving" code, especially code I don't know. I got in trouble before when doing that. I'll just stick to the goal of adding this to VTK."
- Counter-evidence:
  - [!8469](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8469) mwestphal, 2021-10-04: "you could take that out of the if and avoid the smart pointer."

### R055: Use delete[] for arrays allocated with new[]

Rationale: The evidence states that delete[] is required to match new[] allocation and is sufficient without additional checks or resets.

- Scope: C++ sources
- Support: 6 MRs, 6 threads, 2016-06-16 to 2023-03-24
- Reviewers: mwestphal (2), ben.boeckel (1), utkarsh.ayachit (1), cory.quammen (1), dgobbi (1)
- [!9956](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9956) mwestphal, 2023-02-15: "`delete[] this->Stack;` should be enough. No need to reset member, no need to check if allocated."
- [!8784](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8784) dgobbi, 2022-01-11: "The deleter needs `delete[]` to match the `new[]` in `vtk_Py_UTF8ToWide()`, since the strings aren't being created by Python APIs anymore."
- [!3552](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3552) utkarsh.ayachit, 2017-12-14: "should be `delete [] this->TranslationFactor`."

### R058: Compile VTK with VTK_DEBUG_LEAKS enabled to detect and prevent memory leaks.

Rationale: Enabling VTK_DEBUG_LEAKS helps identify memory leaks in VTK objects and tests.

- Scope: C++ sources
- Support: 6 MRs, 6 threads, 2017-01-16 to 2022-07-07
- Reviewers: demarle (3), sujin.philip (1), mwestphal (1), timothee.chabat (1)
- [!9363](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9363) timothee.chabat, 2022-07-07: "please compile with `VTK_DEBUG_LEAKS=ON` to be sure there is no leak when using this reader"
- [!6231](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6231) demarle, 2019-11-26: "If you turn on VTK_DEBUG_LEAKS in your cmake configuration and rebuild VTK you can reproduce the leak that is causing the PIO test to fail."
- [!4271](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4271) demarle, 2018-10-23: "The python tests (ctest -R Python-Quadric) are leaking with this change. I suspect your New needs to be Delete'd or put in a smartpointer I think. Make sure you configure VTK with VTK_DEBUG_LEAKS on t"

### R091: Use raw pointers for VTK objects and arrays, and manage ownership via reference counting or explicit delete[].

*Mixed evidence: check the examples before accepting.*

Rationale: Ownership is managed via reference counting (New/Delete) or explicit delete[] for arrays.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2017-03-13 to 2021-07-15
- Reviewers: jpouderoux (1), mhanwell (1), cory.quammen (1), mwestphal (1)
- [!8147](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8147) cory.quammen, 2021-07-15: "None of the parameters need to be a `vtkSmartPointer<T>` - raw pointers are fine here, e.b., `vtkPoints* interestPoints`. The same is true for the other protected functions."
- [!4262](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4262) mhanwell, 2018-05-09: "It should be `this->Precision == 0` (use of this pointer explicitly in VTK style.)"
- [!2513](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2513) jpouderoux, 2017-06-01: "because we store it for cache purpose in a map."
- Counter-evidence:
  - [!12178](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12178) sankhesh, 2025-06-05: "Do not use unique_ptr with vtk-derived objects. We recommend using `vtkNew` because VTK objects have their own internal reference counting and custom deletion logic, making unique_ptr's ownership sema"
  - [!12472](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12472) mwestphal, 2025-09-24: "vtkMapper calls `this->ColorTextureMap->UnRegister(this)` in different places, so I was not sure how to handle that. Will it break if I use a smart pointer? 100% of the existing mappers (even recent o"

### R094: Reserve vector capacity before push_back to avoid reallocations.

*Mixed evidence: check the examples before accepting.*

Rationale: To avoid copies and memory allocations.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2019-07-23 to 2024-04-23
- Reviewers: charles.gueunet (2), michael.migliore (1), timothee.chabat (1)
- [!10355](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10355) charles.gueunet, 2023-08-24: "With just the change that in a distributed context it is `pieces.reserve(filePieceCount/memoryPieceCount)`"
- [!9821](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9821) timothee.chabat, 2023-01-06: "if you have an approximate idea of the number of elements in these vectors you can call `reserve` to avoid some copy and memory allocation"
- [!5776](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5776) michael.migliore, 2019-07-23: "it is preallocated line 991"
- Counter-evidence:
  - [!2788](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2788) utkarsh.ayachit, 2017-05-06: "note, this sets vector size to MaxEntries, not just reserve space for the same. Any `push_back` after this point will add additional entries."

### R103: Include <memory> and use std::unique_ptr instead of std::auto_ptr for ownership of heap-allocated objects.

Rationale: auto_ptr is deprecated in C++11 and std::unique_ptr should be used instead.

- Scope: all C++ sources
- Support: 4 MRs, 5 threads, 2017-11-22 to 2023-11-15
- Reviewers: robertmaynard (1), michael.migliore (1), charles.gueunet (1), nicolas.vuaille (1), lucas.givord (1)
- [!10638](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10638) lucas.givord, 2023-11-15: "you will need to include `<memory>` to be able to use `std::unique_ptr`"
- [!9448](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9448) nicolas.vuaille, 2022-08-19: "may use a `unique_ptr` to avoid this"
- [!3610](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3610) robertmaynard, 2017-11-22: "this is should be std::unique_ptr. auto_ptr is deprecated in c++11"

### R106: Set pointers to nullptr after deleting or FastDelete to prevent dangling references.

Rationale: to prevent dangling pointer or reference issues after cleanup.

- Scope: C++ sources
- Support: 4 MRs, 5 threads, 2019-05-07 to 2023-11-10
- Reviewers: sebastien.jourdain (2), mwestphal (2), michael.migliore (1)
- [!10697](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10697) mwestphal, 2023-11-10: "this should not be needed, this does not exist after the destructor."
- [!9142](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9142) mwestphal, 2022-05-02: "not needed, you can delete nullptr fixed"
- [!5738](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5738) michael.migliore, 2019-07-11: "I would prefer `this->Locator = nullptr` if exposing the api is necessary"

### R127: Memory allocated with new must be freed with delete.

*Mixed evidence: check the examples before accepting.*

Rationale: To prevent memory leaks.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2016-04-06 to 2021-11-18
- Reviewers: sankhesh (1), kmorel (1), mwestphal (1)
- [!8618](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8618) mwestphal, 2021-11-18: "you need a delete"
- [!1883](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1883) kmorel, 2016-08-29: "It looks like these lines were copied from what is now on lines 1411-1412, but those lines were never deleted. This means it looks like `New` would be called twice when `VTK_DATASET_SURFACE_USE_510_AL"
- [!1402](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1402) sankhesh, 2016-04-06: "`fname` needs to be deleted later. Otherwise, it will leak."
- Counter-evidence:
  - [!3941](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3941) jpouderoux, 2018-02-16: "you cannot `free` a pointer allocated with `new`"

### R141: Deprecate weird iterators in favor of vtk::Range and use vtkSmartPointer to manage VTK iterator objects and avoid manual Delete() calls.

Rationale: To prevent memory leaks from untested or raw pointer usage in iterators.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2015-05-05 to 2025-11-24
- Reviewers: utkarsh.ayachit (1), louis.gombert (1), alexy.pellegrini (1)
- [!12640](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12640) alexy.pellegrini, 2025-11-24: "A good thing to do is maybe deprecate all the weird iterators in favor of vtk:Range."
- [!10983](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10983) louis.gombert, 2024-03-26: "yes, this untested filter used to leak memory"
- [!145](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/145) utkarsh.ayachit, 2015-05-05: "Iterator will leak. I'd suggest switching to using a smart pointer at line #442 (something as follows) and then removeing the iter->Delete() later in this function. vtkSmartPointer<vtkDataObjectTreeIt"

### R151: Users must free the memory returned by the function themselves using the delete operator.

Rationale: The reviewers noted that users need to free the return value and that the caller is responsible for deleting it with delete.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2017-06-06 to 2021-09-29
- Reviewers: jacob (1), jpouderoux (1), timothee.chabat (1)
- [!8457](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8457) timothee.chabat, 2021-09-29: "If you can please check for other use of `vtkOSPRayMaterialLibrary::WriteBuffer` an if thery are correctly freeing memory in other places of VTK. Also specify in the doc that users have to free the re"
- [!2915](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2915) jpouderoux, 2017-06-06: "It is caller's responsibility to delete it with the delete operator."
- [!2636](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2636) jacob, 2018-11-20: "delete [] filename;"

### R157: Use vtkSmartPointer for dataset ownership to avoid manual memory management and potential leaks.

Rationale: To avoid manual memory management and potential leaks.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2018-03-05 to 2022-05-31
- Reviewers: utkarsh.ayachit (2), charles.gueunet (1)
- [!9230](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9230) charles.gueunet, 2022-05-31: "Indeed, it will register the object. I find it dangerous as a dataset / HTG may keep a ref on its locator, so if the locator also keep a ref to the dataset we may have a cyclic dependency (hence a lea"
- [!4449](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4449) utkarsh.ayachit, 2018-07-02: "I'd make this a `vtkSmartPointer<vtkDataSet>` instead and change the `Extract...` methods to simply returns a smart pointer to the dataset."
- [!3913](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3913) utkarsh.ayachit, 2018-03-05: "Use the following: ```c++ vtkSmartPointer<vtkImageData> paddedKernel; paddedKernel.TakeReference(vtkMomentsHelper::padKernel(...)); ```"

## deprecation-abi

### R005: Deprecated methods should be marked with the VTK_DEPRECATED_IN_X_Y_Z macro and include a descriptive message indicating the replacement or reason for deprecation.

*Mixed evidence: check the examples before accepting.*

Rationale: Reviewers stated that deprecated methods need a deprecation macro with a message directing users to the replacement or explaining the deprecation.

- Scope: C++ sources
- Support: 24 MRs, 28 threads, 2015-11-06 to 2025-12-01
- Reviewers: mwestphal (8), ben.boeckel (7), utkarsh.ayachit (2), charles.gueunet (2), spiros.tsalikis (2)
- [!12578](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12578) mwestphal, 2025-12-01: "VTK_DEPRECATED_IN_9_6_0("This method is deprecated, use the other version instead")"
- [!12429](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12429) mwestphal, 2025-09-05: "// VTK_DEPRECATED_IN_9_6_0 vtkHyperTree* vtkHyperTree::CreateInstance(unsigned char factor, unsigned char dimension)"
- [!12223](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12223) mwestphal, 2025-06-20: "please add `// VTK_DEPRECATED_IN_9_5_0` in the Cxx for simpler cleanup"
- Counter-evidence:
  - [!2965](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2965) utkarsh.ayachit, 2017-07-14: "Use `VTK_LEGACY_BODY_REPLACE` so you can tell what's the new method to use in the warning message generated."
  - [!3323](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3323) ben.boeckel, 2017-09-26: "Shouldn't all of the impls of the methods here (and in other classes) get `VTK_LEGACY_BODY` calls?"
  - [!3327](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3327) shawn.waldon, 2017-09-25: "We are only removing stuff that was deprecated at or before VTK 7.1. We can't remove this yet since it hasn't been deprecated long enough."

### R032: Do not remove VTK_ABI_NAMESPACE_END and ensure VTK_ABI_NAMESPACE_BEGIN and VTK_ABI_NAMESPACE_END wrap class forward declarations and are placed correctly to maintain ABI compatibility.

*Mixed evidence: check the examples before accepting.*

Rationale: The evidence states that VTK_ABI_NAMESPACE_END should not be removed and that the BEGIN/END macros are required for ABI compatibility and proper symbol mangling.

- Scope: C++ source files and headers
- Support: 8 MRs, 9 threads, 2023-01-13 to 2024-08-30
- Reviewers: ben.boeckel (2), lucas.givord (2), ryan.krattiger1 (1), thomas.galland (1), svenevs (1)
- [!11394](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11394) mwestphal, 2024-08-30: "should not be removed"
- [!10762](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10762) charles.gueunet, 2024-01-05: "Need `VTK_ABI_NAMESPACE_BEGIN / END` around those forward declare (see `Common/Core/Testing/Cxx/vtkTestNewVar.h` for an example)"
- [!10676](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10676) svenevs, 2024-01-01: "set(_vtk_abi_namespace_name_regex "^[a-zA-Z0-9_]+$") is all we allow in now, anybody who previously had `-DVTK_ABI_NAMESPACE_NAME='some_namespace __attribute__ ((visibility ("hidden")))'` will get a c"
- Counter-evidence:
  - [!9612](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9612) mwestphal, 2022-10-13: "The rule is that `VTK_ABI_NAMESPACE_*` must be the *innermost* namespace. No namespaces may be inside of it as it otherwise causes ambiguity when referring to types: ```c++ inline namespace ABI { name"
  - [!9636](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9636) ben.boeckel, 2022-10-20: "My thinking was that there is no need to tinker with names inside of the blank namespace. There is a VTK_ABI_NAMESPACE_BEGIN after the namespace."
  - [!10822](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10822) svenevs, 2024-01-15: "#else defines `VTK_ABI_NAMESPACE_MANGLE(x) x`"

### R037: Deprecate old method names when new overloads or replacements are added to avoid confusion and guide users toward the updated API.

*Mixed evidence: check the examples before accepting.*

Rationale: Reviewers stated that old methods should be deprecated when new methods are added to prevent confusion between overloads and to guide users toward the new API.

- Scope: C++ sources
- Support: 8 MRs, 10 threads, 2020-09-29 to 2025-10-01
- Reviewers: mwestphal (3), spiros.tsalikis (2), cory.quammen (1), yohann.bearzi (1), danlipsa (1)
- [!12452](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12452) mwestphal, 2025-10-01: "because otherwise in vtkUnstructuredGrid, you will have `vtkDataArray* GetCellTypes();` `void GetCellTypes(vtkCellTypes* types)` In my opinion, that would be confusing."
- [!12464](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12464) timothee.couble, 2025-09-16: "Should the old methods be deprecated @mwestphal? Yes, see https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8262/diffs#3ca99774cc16574f697fd6c7b48b4a668a4cd3f0"
- [!11596](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11596) nicolas.vuaille, 2024-10-31: "For backward compatibility, you will need to create another method, make the old call the new with a default param and deprecate the old."
- Counter-evidence:
  - [!10165](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10165) demarle, 2023-05-18: "I suggest leave the old string in and simply override both. There is no harm in leaving the old "..2" string here. Applications/builds that use the new CPDM will simply not exercise it and removing wi"

### R048: Deprecated members should be replaced with new methods and include a deprecation message explaining why they are being removed.

*Mixed evidence: check the examples before accepting.*

Rationale: The evidence states that deprecated methods should be replaced with new methods and that deprecation messages should explain the reason for removal.

- Scope: C++ sources
- Support: 7 MRs, 9 threads, 2022-04-26 to 2025-12-01
- Reviewers: mwestphal (6), cory.quammen (1), jean.fechter (1), lucas.givord (1)
- [!12220](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12220) jean.fechter, 2025-06-18: "I think this should mention that the method did nothing, which is why it is being removed. "No longer used." makes it sound like it was useful before."
- [!11988](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11988) mwestphal, 2025-04-03: "it is used by a deprecated method. I added a DEPREC comment here to remove them alongside with the call."
- [!10902](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10902) mwestphal, 2024-04-05: "since this can be changed by another anyone inheriting vtkHDFReader, true retro compatibility is way more complex. You basically needs to replace all usage of `HasTemporalData` by a `GetHasTemporalDat"
- Counter-evidence:
  - [!9044](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9044) charles.gueunet, 2022-04-06: "Why do you need to force a disabled version of the method ? The deprecation may be enough... In the first stage I figured that we would add the deprecation (ie, don't use this thing for compilation an"
  - [!10902](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10902) mwestphal, 2024-04-05: "GetHasTransientData will always fallback to GetHasTemporalData() so I don't see any use case than I can miss, is it true?"

### R070: Deprecate public usage of a class/function or methods and enums before removing them to maintain retrocompatibility.

Rationale: Deprecation avoids breaking existing code and maintains retrocompatibility.

- Scope: public types, methods, enums, parameters, and classes/functions
- Support: 6 MRs, 8 threads, 2021-01-15 to 2025-08-11
- Reviewers: spiros.tsalikis (3), mwestphal (2), ben.boeckel (1), drpeterfranz (1), alexy.pellegrini (1)
- [!12363](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12363) alexy.pellegrini, 2025-08-11: "This is a breaking change, only deprecate for now :)"
- [!11363](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11363) spiros.tsalikis, 2024-09-04: "Deprecate instead of removing"
- [!10165](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10165) mwestphal, 2023-05-18: "Many non-retrocompatible changes in this MR. Was it voluntary to not deprecate methods and enums that have been removed ?"

### R073: Replace VTK_ FUTURE_ CONST with const in new classes where the underlying API supports it, ensuring const-correctness for public APIs and method return types without breaking const contexts.

*Mixed evidence: check the examples before accepting.*

Rationale: VTK_ FUTURE_ CONST is only needed when a method cannot be const due to internal non-const usage, and consting is retro-compatible while unconsting is not.

- Scope: C++ sources
- Support: 5 MRs, 5 threads, 2022-02-22 to 2025-07-23
- Reviewers: ben.boeckel (2), seanm (1), louis.gombert (1), spiros.tsalikis (1)
- [!12230](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12230) spiros.tsalikis, 2025-07-23: "all VTK_FUTURE_CONST can be replaced with const, given that this is a new class"
- [!12229](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12229) louis.gombert, 2025-07-09: "yes, unconsting is not-retrocompatible, consting is retro-compatible. `VTK_FUTURE_CONST` is only needed when a method cannot be set `const` because of method used internally which are not const yet."
- [!11575](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11575) seanm, 2024-11-05: "VTK_FUTURE_CONST vtkPlane* GetTopPlane() { return this->TopPlane; } then: /VTK/Interaction/Widgets/vtkImplicitFrustumRepresentation.cxx:1273:57: error: no matching member function for call to 'GetNorm"
- Counter-evidence:
  - [!1455](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1455) alliepiper16, 2016-04-25: "Was there a reason for this? Most of VTK is not const-correct, and these changes will break our virtual API."
  - [!5841](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5841) yohann.bearzi, 2019-08-08: "VTK objects are not `const` safe yet. This issue will be addressed in the future, but for now it would be better to not put `const` VTK objects as parameters to avoid the use of `const_cast`."
  - [!6771](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6771) tjcorona, 2020-04-20: "The main issue with making VTK const correct is whether the benefit outweighs the cost of any updates that would be required to consumers of VTK - that's not quite clear."

### R076: Deprecation macros should be updated to reflect the current or next release version number they target.

*Mixed evidence: check the examples before accepting.*

Rationale: The evidence shows reviewers require deprecation macros to align with the specific release version they target or the current release version.

- Scope: C++ sources
- Support: 5 MRs, 6 threads, 2021-10-04 to 2024-11-14
- Reviewers: tiffany.chhim (2), spiros.tsalikis (2), ben.boeckel (1), cory.quammen (1)
- [!11639](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11639) cory.quammen, 2024-11-14: "Since this won't go in 9.4, this should be VTK_DEPRECATED_IN_9_5_0, right?"
- [!9812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9812) spiros.tsalikis, 2023-12-12: "Change VTK_DEPRECATED_IN_9_3_0 -> VTK_DEPRECATED_IN_9_4_0"
- [!8975](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8975) ben.boeckel, 2022-09-08: "These should use 9_3_0 now."
- Counter-evidence:
  - [!10963](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10963) lucas.givord, 2024-03-13: "yes it is expected, and deprecation are not bugfixes and should not be backported imo."

### R089: Add a release note under Documentation/release/dev for any API change or breakage.

Rationale: Release notes are the designated place to document API changes and breaks.

- Scope: Documentation/release/dev
- Support: 5 MRs, 5 threads, 2021-05-29 to 2025-12-26
- Reviewers: ben.boeckel (3), mwestphal (1), acbauer (1)
- [!12746](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12746) ben.boeckel, 2025-12-26: "Release notes mentioning the removed APIs should be added."
- [!8832](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8832) ben.boeckel, 2022-03-04: "There are some API changes here, but they're not documented in the release note."
- [!8740](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8740) ben.boeckel, 2021-12-15: "A release note about the new parameter would be useful as well I think."

### R102: Replace deprecated VTK classes and wrappers with their modern equivalents.

Rationale: The reviewers stated that deprecated classes and wrappers need to be changed to their modern equivalents.

- Scope: C++ source files
- Support: 4 MRs, 5 threads, 2017-10-26 to 2025-10-29
- Reviewers: nicolas.vuaille (3), dgobbi (1), kmorel (1)
- [!12551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12551) nicolas.vuaille, 2025-10-29: "It is used. It needs to be changed because `vtkConstantUnsignedCharArray` is deprecated."
- [!12136](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12136) nicolas.vuaille, 2025-06-11: "Also deprecated version is now 9.6 ... Sorry for that :smile:"
- [!10769](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10769) kmorel, 2024-06-28: "`DataArrayToArrayHandle` is deprecated (see !10763). You should use either `vtkDataArrayToArrayHandle` or `vtkDataArrayToUnknownArrayHandle`."

### R133: When changing a virtual method signature or public API, add a deprecated wrapper before removing the old version.

*Mixed evidence: check the examples before accepting.*

Rationale: This preserves retro compatibility while allowing the old API to be removed later.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2019-07-29 to 2023-03-22
- Reviewers: jpouderoux (1), timothee.chabat (1), mwestphal (1)
- [!10072](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10072) mwestphal, 2023-03-22: "this is breaking retro compat (inheritance). you would need to deprecate this method."
- [!9170](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9170) timothee.chabat, 2022-05-10: "you're changing the public API of a class, which is not good. Please make a new function, and either deprecate this one or leave it as it is (I woulnd't mind leaving this one as it is since it still d"
- [!5723](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5723) jpouderoux, 2019-07-29: "This (nice) change breaks API compatibility. Shouldn't we keep the previous prototype as a deprecated one before stripping it out?"
- Counter-evidence:
  - [!9142](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9142) mwestphal, 2022-05-05: "this is not ok, break retro compat"
  - [!9142](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9142) mwestphal, 2022-05-05: "this is not ok, break retro compat"

### R174: Avoid using GetVoidPointer and prefer using vtk::DataArrayValueRange (or DataArrayValueRange to GetPointer) for iterators and array access.

Rationale: Reviewers stated that GetVoidPointer should be deprecated in favor of array dispatch or DataArrayValueRange for proper SOA compatibility and easier iterators.

- Scope: C++ sources
- Support: 3 MRs, 5 threads, 2020-06-10 to 2022-12-02
- Reviewers: julien.fausty (3), sankhesh (1), mwestphal (1)
- [!9710](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9710) julien.fausty, 2022-12-02: "Avoid using the `GetVoidPointer` prefer using the ranges provided by `vtk::DataArrayValueRange` for example for easy iterators."
- [!9631](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9631) mwestphal, 2022-10-16: "The right way to fix this issue is to deprecate GetVoidPointer() and use array dispatch. Nonetheless, it's important for SOA to properly work. So, either we go for a temporary solution like this, or w"
- [!6983](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6983) sankhesh, 2020-06-10: "Removes use of GetVoidPointer which is to be deprecated as described in https://blog.kitware.com/working-with-vtkdataarrays-2019-edition/"

### R195: Deprecate protected methods.

Rationale: They are protected, so they need deprecation.

- Scope: C++ sources
- Support: 3 MRs, 4 threads, 2024-05-24 to 2024-12-04
- Reviewers: mwestphal (2), thomas.galland (1), lucas.givord (1)
- [!11725](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11725) lucas.givord, 2024-12-04: "I think that it is in the 9.4.0 and as it's a protected method we need to deprecate it"
- [!11652](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11652) mwestphal, 2024-11-08: "this method is technically protected, so it needs deprecation"
- [!11161](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11161) thomas.galland, 2024-05-24: "I think these methods can be renamed (`statistics` is maybe a bit generic here) Also, better set them private by default (for depreciation reasons), it will be easy to move them protected if needed in"

## naming

### R021: Member variables should be named using PascalCase with an uppercase first letter.

*Mixed evidence: check the examples before accepting.*

Rationale: The reviewers stated that member variables should follow PascalCase naming and start with a capital letter.

- Scope: C++ sources
- Support: 11 MRs, 11 threads, 2016-03-08 to 2024-12-03
- Reviewers: cory.quammen (3), will.schroeder (1), jpouderoux (1), LucasGandelKitware (1), michael.migliore (1)
- [!11567](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11567) jaswant.panchumarti, 2024-12-03: "Convert member variables to `PascalCase` instead of `camelCase`"
- [!11247](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11247) cory.quammen, 2024-07-12: "I would capitalize these two member names."
- [!9663](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9663) mwestphal, 2022-11-02: "members starts with a Capital letter."
- Counter-evidence:
  - [!4707](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4707) jpouderoux, 2018-09-26: "All members should be in CamelCase."

### R046: Use lowercase for boolean parameter and variable names.

*Mixed evidence: check the examples before accepting.*

Rationale: Uppercase is reserved for internal fields and boolean names should be lowercase for readability and consistency.

- Scope: C++ sources
- Support: 7 MRs, 7 threads, 2016-10-27 to 2024-03-07
- Reviewers: mwestphal (2), LucasGandelKitware (1), dgobbi (1), timothee.chabat (1), thomas.galland (1)
- [!10914](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10914) charles.gueunet, 2024-03-07: "`UseCache` switch to `useCache`, uppercase is for internal fields"
- [!10223](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10223) thomas.galland, 2023-05-23: "`enabling` -> enable ? It's just for readability, so that we get more easily the difference when reading `if (enabling && !enabled)`. Not sure we need to rename the parameter`"
- [!9567](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9567) timothee.chabat, 2022-09-26: "I don't think boolean properties needs `Active` at the end since it's already pretty much self explenatory (-> `warp->SideWallsOn()` for example)."
- Counter-evidence:
  - [!3539](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3539) jpouderoux, 2017-11-07: "'highlight' is a whole word, so rename to `HighlightPlot`."

### R068: Use camelCase for identifiers.

Rationale: Reviewers stated a preference for camelCase naming in their comments.

- Scope: All C++ sources
- Support: 6 MRs, 6 threads, 2020-09-02 to 2025-11-28
- Reviewers: mwestphal (4), julien.fausty (1), mathurin.lemarie (1)
- [!12574](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12574) mathurin.lemarie, 2025-11-07: "All of this should stay in camel case"
- [!11678](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11678) mwestphal, 2024-11-18: "use camelCase in this file I think"
- [!12655](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12655) mwestphal, 2025-11-28: "worth camelCase"

### R069: Prefix enum names with vtk and use underscores to separate words, with the first value explicitly set and subsequent values incrementing by one, and name plural forms consistently with VTK conventions.

Rationale: To avoid warnings and name collisions with existing VTK macros and to follow established naming patterns in VTK enums.

- Scope: C++ source files
- Support: 6 MRs, 6 threads, 2020-11-04 to 2025-07-04
- Reviewers: cory.quammen (2), julien.fausty (2), ben.boeckel (1), lucas.givord (1)
- [!12228](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12228) lucas.givord, 2025-07-04: "We need to make it different from `VTK_YZ_PLANE` and such. If not, we have warnings."
- [!11741](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11741) cory.quammen, 2024-12-09: "I don't think it's a rule, but many other enums in VTK terminate with an option starting with `NUM_`, e.g., `vtkDataSetAttributes::AttributeTypes::NUM_ATTRIBUTES`, `vtkGeometryFilterHelper::NUM_CELL_T"
- [!10101](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10101) julien.fausty, 2023-03-31: "same comment as above on the `vtk` prefix. Especially if you put the enums in the class scope"

### R081: Use descriptive variable names that reflect their purpose and context.

Rationale: The reviewers stated that unclear or non-descriptive names like 'd', 't', 'eRDA', or 'inCDTemp' are problematic and should be improved to reflect purpose and context.

- Scope: C++ sources
- Support: 5 MRs, 7 threads, 2017-08-18 to 2025-10-10
- Reviewers: jpouderoux (3), mwestphal (2), timothee.chabat (1), michael.migliore (1)
- [!9126](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9126) timothee.chabat, 2022-04-26: "better naming (`shaderFunction', 'signature', 'shaderCode', ...')"
- [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) jpouderoux, 2020-03-27: "If swap has been done during reading step, is it a useful public information? At least var should be name "SwappedAxis" instead?"
- [!3127](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3127) mwestphal, 2017-09-12: "d is not a good variable name"

### R087: Class names should follow the pattern of existing VTK Python wrappers and not include 'vtk', 'Widget', or 'Q' prefixes unless the class extends from Widget or QObject.

Rationale: The evidence states that class names should follow existing VTK Python wrapper patterns and avoid 'vtk', 'Widget', or 'Q' prefixes unless the class extends from Widget or QObject.

- Scope: Python wrapping
- Support: 5 MRs, 5 threads, 2019-04-18 to 2022-08-08
- Reviewers: michael.migliore (2), jpouderoux (1), mwestphal (1), adam-grant-hendry (1)
- [!9443](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9443) adam-grant-hendry, 2022-08-08: "This should also be `SwipeGesture`, not `QSwipeGesture`"
- [!6959](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6959) mwestphal, 2020-06-01: "I like your proposal `QVTKRenderWidget` for the interface, but it should not have `Widget` or `Q` since that interface does no extend from `Widget` or `QObject`."
- [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) michael.migliore, 2020-03-06: "remove `vtk` prefix for class methods"

### R088: Use clear, descriptive, and specific singular names for enums, avoiding generic or plural names that imply multiple values.

Rationale: Enums should be named with specific, descriptive, and singular terms to avoid implying multiple values can be combined and to make their purpose clear.

- Scope: all C++ sources
- Support: 5 MRs, 5 threads, 2020-09-29 to 2025-11-18
- Reviewers: mwestphal (2), cory.quammen (1), julien.fausty (1), leon.victor (1)
- [!12611](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12611) mwestphal, 2025-11-18: "use better namings for your enums: eg: `INTER_STATE_OUTSIDE`"
- [!11358](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11358) leon.victor, 2024-08-01: "I think that enum name is not right. `IndexingMode::Points` would be clearer, maybe `IndexingMode::IndexedOnPoints` if you prefer"
- [!10143](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10143) julien.fausty, 2023-04-21: "I think we should rename these. What do you think of: ```suggestion:-4+0 enum CellStrategy3D { USE_VOXELS, DECOMPOSE_POLYHEDRA };```"

### R097: Rename variables to be consistent with existing naming patterns and reduce the chance of name conflicts.

Rationale: To ensure consistency with the codebase and reduce the chance of name conflicts in the future.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2017-01-12 to 2022-07-14
- Reviewers: brad.king (1), alouis (1), timothee.chabat (1), jcfr (1)
- [!9381](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9381) jcfr, 2022-07-14: "For consistency with the variable name, I suggest `MAX_STACK_ARRAY_SIZE` -> `MAX_SCRATCH_ARRAY_SIZE` I concur, it will also reduce the chance of name conflicts in the future, as it is a little more sp"
- [!9231](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9231) timothee.chabat, 2022-06-01: "please rename `in_volumetricScatteringBlending` for case consistency (if it is already consistent)"
- [!2843](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2843) alouis, 2017-05-23: "it refers to the filename "cth.vtr""

### R107: Capitalize method names using PascalCase and ensure they begin with an uppercase letter and a verb.

Rationale: Reviewers stated that method names should be capitalized, begin with an uppercase letter, and start with a verb.

- Scope: all C++ sources
- Support: 4 MRs, 4 threads, 2019-05-22 to 2023-08-07
- Reviewers: mwestphal (1), jpouderoux (1), francois.mazen (1), julien.fausty (1)
- [!10233](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10233) julien.fausty, 2023-08-07: "Also, please capitalize method names."
- [!7897](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7897) francois.mazen, 2021-04-27: "I foster method name that begin with a verb, so I would suggest a name like `SynchronizeDataArraySelectionRecursively`"
- [!5588](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5588) jpouderoux, 2019-08-19: "return => Return"

### R111: Rename functions to match their actual implementation and all invocations, using clear and correct names without typos.

Rationale: Reviewers stated that function names should reflect what the function does and be consistent across definitions and calls, and that names should be clear and free of typos.

- Scope: C++ source files
- Support: 4 MRs, 4 threads, 2020-03-06 to 2024-05-14
- Reviewers: michael.migliore (1), cory.quammen (1), dcthomp (1), spiros.tsalikis (1)
- [!10852](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10852) spiros.tsalikis, 2024-05-14: "This function name would probably be better if it was EnqueParticleToAnotherProcess, since it does not actually do any Controller Call."
- [!10538](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10538) dcthomp, 2023-09-25: "You renamed the function to `TestDegenerateCell()` but didn't rename the invocation."
- [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) michael.migliore, 2020-03-06: "I would rename this function to `RGBEReaderUpdateSlice`, what do you think? Yes more verbose !"

### R124: Use PascalCase for function names.

*Mixed evidence: check the examples before accepting.*

Rationale: Reviewers stated that PascalCase is clearer and more consistent than camelCase.

- Scope: all C++ sources
- Support: 3 MRs, 4 threads, 2021-07-15 to 2024-03-28
- Reviewers: LucasGandelKitware (2), cory.quammen (1), louis.gombert (1)
- [!11001](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11001) louis.gombert, 2024-03-28: "`AreAllFacesPlanar` would be a better name :smile:"
- [!9602](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9602) LucasGandelKitware, 2023-01-09: "zccompatGetFrustumCameraOffset -> zccompatSetFrustumAttributeF32 ?"
- [!8147](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8147) cory.quammen, 2021-07-15: "Please capitalize the `i` in `interpolateVector`"
- Counter-evidence:
  - [!9193](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9193) timothee.chabat, 2022-05-18: "CamelCase for function and members, and camelCase for local variables and parameters"
  - [!10475](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10475) dcthomp, 2023-09-04: "`HideInternalCellBoundaries` should be `hideInternalCellBoundaries` (lowercase initial character for function parameters)."

### R134: Use enum class and prefix enum values with the class name using the scope resolution operator.

*Mixed evidence: check the examples before accepting.*

Rationale: To avoid polluting the class scope and ensure proper qualification of enum values.

- Scope: C++ sources
- Support: 3 MRs, 4 threads, 2020-05-13 to 2021-11-17
- Reviewers: utkarsh.ayachit (2), mwestphal (1), francois.mazen (1)
- [!8650](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8650) francois.mazen, 2021-11-17: "Change type to `JointMode`"
- [!8408](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8408) utkarsh.ayachit, 2021-09-13: "`Mode::Squash` would only work everywhere for `enum class`. Here, use `vtkPartitionBalancer::Squash`.`"
- [!6101](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6101) mwestphal, 2020-05-13: "vtkVectorFieldTopology::DEGENERATE2D and other enums as well"
- Counter-evidence:
  - [!9792](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9792) julien.fausty, 2022-12-21: "IMO, the fact this is already in the class is scope enough, you can just call it `SearchMethod`"

### R159: Avoid naming variables the same as member variables to prevent confusion.

Rationale: To prevent confusion with existing member variables and the public API.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2018-05-31 to 2020-03-25
- Reviewers: LucasGandelKitware (1), jpouderoux (1), dcthomp (1)
- [!6620](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6620) dcthomp, 2020-03-25: "Can we name this something other than `fn` so that it is harder to confuse with `Shim.fn`?"
- [!6256](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6256) jpouderoux, 2019-12-04: "We should rename `CSVReader` to `InternalReader` for instance"
- [!4326](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4326) LucasGandelKitware, 2018-05-31: "Please use explicit names for member variable : `this->RenderWindow`"

### R161: Use the suffix "Internal" or "Internals" for private classes.

Rationale: It is easy to say, not ambiguous, and has precedent in VTK.

- Scope: C++ source files
- Support: 3 MRs, 3 threads, 2018-09-26 to 2024-07-29
- Reviewers: jpouderoux (1), cory.quammen (1), dgobbi (1)
- [!11352](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11352) dgobbi, 2024-07-29: "My preference is "Internal" or "Internals" as a suffix. Easy to say, not ambiguous, and plenty of precedent. "Impl" isn't bad either, but its meaning is a bit more specific, not all private classes ar"
- [!5773](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5773) cory.quammen, 2019-07-25: "How about changing this to `vtk3DLinearGridInternal`. There is precedent in VTK for using the `Internal` suffix to signify a class is private."
- [!4707](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4707) jpouderoux, 2018-09-26: "Internal => Internals"

### R179: Avoid leading underscores in variable names and use trailing underscores for member variables to prevent conflicts with reserved identifiers and potential methods.

Rationale: To prevent conflicts with reserved identifiers and potential methods.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2021-02-09 to 2022-01-02
- Reviewers: olesen (1), dgobbi (1), ben.boeckel (1)
- [!8769](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8769) ben.boeckel, 2022-01-02: "I guess this should get renamed too? Indeed."
- [!8763](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8763) dgobbi, 2021-12-22: "Even though it isn't capitalized, should `_a_` be changed as well for consistency?"
- [!7600](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7600) olesen, 2021-02-09: "Couldn't we call these `data_` and `size_` etc? Otherwise can get ugly with data() and size() methods in the future."

### R183: Every free function should be placed in the "vtk" namespace.

Rationale: To avoid namespace symbol collisions.

- Scope: all C++ sources
- Support: 3 MRs, 3 threads, 2022-06-08 to 2025-06-05
- Reviewers: cory.quammen (1), timothee.chabat (1), sankhesh (1)
- [!12178](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12178) sankhesh, 2025-06-05: "1. Every free function should be in the "vtk" namespace. Rationale: Namespace symbol collision avoidance"
- [!9691](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9691) timothee.chabat, 2022-11-22: "I would use `namespace vtkCompositeArray` here (if possible ?), as we want to limit the number of symbols the user has access to IMO"
- [!9224](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9224) cory.quammen, 2022-06-08: "`EDGE_LIST` is a combo of two common words, so there is danger of collision with a type of the same name in other libraries. Suggest `vtkMarchingCubesPolygonCasesEdgeListType` instead to effectively n"

### R189: Reviewers should rename variables and methods to more descriptive names.

Rationale: Reviewers stated that renaming improves clarity and reflects purpose.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2023-01-17 to 2025-04-11
- Reviewers: mwestphal (2), lucas.givord (1)
- [!11986](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11986) mwestphal, 2025-04-11: "please rename `R`"
- [!11271](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11271) lucas.givord, 2024-07-05: "rename it CreateHierarchicalZBuffer()"
- [!9792](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9792) mwestphal, 2023-01-17: "please rename x"

## compiler-warnings

### R019: If a class has virtual methods or overrides, its destructor should be virtual and marked with override.

*Mixed evidence: check the examples before accepting.*

Rationale: to avoid warnings and ensure proper inheritance behavior.

- Scope: C++ source files
- Support: 12 MRs, 13 threads, 2018-01-10 to 2024-05-29
- Reviewers: ken-martin (6), charles.gueunet (5), sankhesh (1), thomas.galland (1)
- [!11165](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11165) thomas.galland, 2024-05-29: "here and in other classes: if not overridden, still add `~vtkWebGPUComputePipeline() override = default;`"
- [!11128](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11128) charles.gueunet, 2024-05-16: "virtual destructor instead, as it is intended for inheritance :grinning:"
- [!9193](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9193) charles.gueunet, 2022-05-17: "destructor should be virtual"
- Counter-evidence:
  - [!4914](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4914) cory.quammen, 2018-11-26: "It's a virtual method call in the destructor. The destructor code for any derived classes will already have been called by this point, so calling any override-able virtual methods is unsafe."

### R030: Remove unused variables or mark them static to suppress compiler warnings.

Rationale: The reviewers stated that unused variables generate compiler warnings and should be removed or addressed.

- Scope: C++ source files
- Support: 9 MRs, 9 threads, 2017-01-17 to 2023-11-10
- Reviewers: mwestphal (6), dgobbi (2), demarle (1)
- [!10695](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10695) dgobbi, 2023-11-10: "warning: unused variable 'HASH_ERROR' [-Wunused-const-variable] warning: unused variable 'HASH_LINE' [-Wunused-const-variable] warning: unused variable 'HASH_PRAGMA' [-Wunused-const-variable]"
- [!9125](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9125) mwestphal, 2023-06-21: "you have a warning to fix: Core/vtkRenderer.cxx:1513:16: warning: unused variable 'closestProp' [-Wunused-variable]"
- [!9398](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9398) mwestphal, 2022-08-07: "Interaction/Widgets/vtkCompassWidget.cxx:124:29: warning: unused variable 'representation' [-Wunused-variable]"

### R034: Use the vtkNotUsed macro to suppress compiler warnings for unused parameters instead of deleting them.

*Mixed evidence: check the examples before accepting.*

Rationale: Deleting unused parameters can cause compiler warnings, especially with unnamed arguments, so wrapping them in vtkNotUsed silences those warnings.

- Scope: C++ sources
- Support: 8 MRs, 8 threads, 2015-08-19 to 2025-12-10
- Reviewers: mwestphal (2), cory.quammen (1), dgobbi (1), drpeterfranz (1), ben.boeckel (1)
- [!10758](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10758) mwestphal, 2023-12-13: "use vtkNotUsed to avoid unused warnings"
- [!10587](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10587) charly.bollinger, 2023-10-11: "remove comment and replace with `vtkNotUsed(loc_id)`"
- [!9542](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9542) ben.boeckel, 2022-09-11: "This can just be an unnamed parameter to the lambda (`vtkNotUsed`-wrapped)."
- Counter-evidence:
  - [!2872](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2872) jpouderoux, 2017-05-24: "Remove the comment and add the keyword VTK_DELETE_FUNCTION before the semicolumn (those comments apply in this class and everywhere else)"

### R059: Do not compare integer expressions of different signedness directly; use static_cast to fix the warning.

Rationale: The reviewers stated that such comparisons generate warnings and must be fixed to keep the dashboard clean.

- Scope: C++ sources
- Support: 6 MRs, 6 threads, 2018-11-01 to 2025-03-31
- Reviewers: mwestphal (2), cory.quammen (1), ken-martin (1), sebastien.jourdain (1), yohann.bearzi (1)
- [!12033](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12033) mwestphal, 2025-03-31: "warning: comparison of integer expressions of different signedness: 'int' and 'std::vector<vtkGLTFDocumentLoader::Accessor>::size_type' {aka 'long unsigned int'} [-Wsign-compare]"
- [!7701](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7701) mwestphal, 2021-03-01: "the compiler cannot know if `node.Camera` is unsigned so it raises a sign mismatch warning here."
- [!7260](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7260) yohann.bearzi, 2020-09-28: "You have to `static_cast` one way or another so you don't compare signed integer with unsigned integer."

### R084: Fix all compiler warnings before approval or merging.

Rationale: The reviewers stated that unhandled or newly introduced compiler warnings must be addressed before approval or merging.

- Scope: all C++ sources
- Support: 5 MRs, 5 threads, 2018-03-22 to 2023-02-21
- Reviewers: ken-martin (3), demarle (1), vbolea (1)
- [!9869](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9869) vbolea, 2023-02-21: "On another topic we need to address the newly introduced compiler warnings before approval."
- [!8411](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8411) ken-martin, 2021-09-16: "At least one compiler warning introduced I believe. Take a look through the output and try pushing a fix for any you see. Thanks!"
- [!5490](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5490) ken-martin, 2019-05-06: "Please fix warnings prior to merging."

### R090: Replace VTK_OVERRIDE with override

*Mixed evidence: check the examples before accepting.*

Rationale: VTK_OVERRIDE is deprecated and will be removed as a C++11 compiler is required

- Scope: C++ sources
- Support: 4 MRs, 5 threads, 2016-09-07 to 2018-12-04
- Reviewers: jcfr (1), robertmaynard (1), utkarsh.ayachit (1), demarle (1), jpouderoux (1)
- [!1455](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1455) jcfr, 2018-12-04: "the compiler should warn about that particular case because the derived class's implementation will hide the base class's method"
- [!3647](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3647) jpouderoux, 2017-12-04: "VTK_OVERRIDE keyword is deprecated, use `override` instead"
- [!3308](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3308) demarle, 2017-10-13: "replace VTK_OVERRIDE with override (a recent VTK change obsoleted the macro since we no longer need c++97 compatibility)"
- Counter-evidence:
  - [!2872](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2872) jpouderoux, 2017-05-24: "Remove `virtual`keyword and add `VTK_OVERRIDE` at the end of the prototype declaration (see C++11 related rules)"
  - [!2917](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2917) demarle, 2017-06-07: "This needs VTK_OVERRIDE because c++11 constructs are now required."
  - [!2917](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2917) jpouderoux, 2017-06-08: "VTK_OVERRIDE instead"

### R131: Use vtkMath::Min/Max instead of custom or std:: min/max functions.

*Mixed evidence: check the examples before accepting.*

Rationale: To ensure consistency with the codebase and avoid MSVC compatibility or code generation issues.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2018-08-30 to 2024-09-04
- Reviewers: cory.quammen (2), spiros.tsalikis (1)
- [!11363](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11363) spiros.tsalikis, 2024-09-04: "WHy not just use vtkMath::Min/Max? I was just inspired by "Common/Core/vtkDataArrayPrivate.txx". Thus no reason to not use vtkMath::Min/Max Replacement by vtkMath::Min/Max done !"
- [!5367](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5367) cory.quammen, 2019-04-03: "Do we support MSVC 2013? If so, it is safer to use `vtkMath::Min`/`Max` to avoid problem in MSVC 2013 (see !4255)."
- [!4637](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4637) cory.quammen, 2018-08-30: "Please use `vtkMath::Max()` instead of `std::max` here and below. There is a problem with code generation in MSVC when using `std::max/std::min`. See https://gitlab.kitware.com/vtk/vtk/merge_requests/"
- Counter-evidence:
  - [!4239](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4239) utkarsh.ayachit, 2018-04-30: "want to switch to using `std::max`, `std::min`?"

### R155: Fix warnings before merging

Rationale: To avoid nightly dashboard issues

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2017-07-10 to 2020-10-29
- Reviewers: dgobbi (1), utkarsh.ayachit (1), LucasGandelKitware (1)
- [!7364](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7364) LucasGandelKitware, 2020-10-29: "Warnings have been fixed."
- [!6290](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6290) utkarsh.ayachit, 2020-02-13: "there are a few warnings. once you've fixed those, feel free to merge."
- [!3008](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/3008) dgobbi, 2017-07-10: "But I recommend that the `double zaxis[3] = {0, 0, 1};` issue above be fixed before merge, because it's likely to cause warnings on some of the nightly dashboards."

### R178: Suppress unused variables or parameters with (void) to avoid compiler warnings.

Rationale: To prevent compiler warnings about unused variables or parameters.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2021-01-15 to 2025-12-11
- Reviewers: charles.gueunet (1), dgobbi (1), jaswant.panchumarti (1)
- [!12709](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12709) jaswant.panchumarti, 2025-12-11: "does it warn that `error` is unused? `(void)error`"
- [!9135](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9135) dgobbi, 2022-05-03: "Ditto. This will complain that `argc`, `argv` are undefined."
- [!7516](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7516) charles.gueunet, 2021-01-15: "To suppress a compilation warning about the return value being not used."

### R191: Explicitly convert boolean values using !! to avoid implicit double-to-bool conversion.

Rationale: Some compilers do not like implicit boolean conversion and it is sketchy.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2022-12-29 to 2025-12-09
- Reviewers: timothee.chabat (2), spiros.tsalikis (1)
- [!12321](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12321) spiros.tsalikis, 2025-12-09: "Some compilers do not like implicit boolean conversion. `!!` makes the conversion explicit."
- [!9868](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9868) timothee.chabat, 2023-01-30: "avoid implicit conversion from double to bool"
- [!9806](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9806) timothee.chabat, 2022-12-29: "here and everywhere else, implicit conversion from `double` to `bool` is sketchy. Should `== 0.0` even happen ?"

## build-cmake

### R028: Commit messages must be concise, informative, and follow a specific format with a short title, an empty line, and a detailed description.

Rationale: Reviewers emphasized the need for concise and informative messages, a short title, and a clear structure with a blank line separating the title from the description.

- Scope: all C++ sources
- Support: 9 MRs, 9 threads, 2016-03-22 to 2023-03-20
- Reviewers: cory.quammen (2), julien.fausty (2), utkarsh.ayachit (1), demarle (1), mwestphal (1)
- [!7521](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7521) mwestphal, 2023-03-20: "Yes, ammend your commit message."
- [!10059](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10059) julien.fausty, 2023-03-17: "There is no strict requirements regarding git commit messages syntax but try to be as informative as possible: git commit -m "Short yet informative commit message". A good rule of thumb for your short"
- [!10052](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10052) julien.fausty, 2023-03-13: "Please prefix your commit message with `HyperTreeGridAxisClip:` (or something similarly informative) so that it is explicit which area of VTK the fixes were applied to"

### R078: Mark dependencies as PRIVATE_DEPENDS if they are not part of the public API.

Rationale: Marking a dependency as private avoids adding it to include/link lines where it isn't needed.

- Scope: CMake module files
- Support: 5 MRs, 5 threads, 2016-04-14 to 2023-01-03
- Reviewers: utkarsh.ayachit (2), mwestphal (2), ben.boeckel (1)
- [!9499](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9499) ben.boeckel, 2023-01-03: "Sorry, moved to `PRIVATE_DEPENDS`."
- [!6101](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6101) mwestphal, 2020-06-02: "Yes, the new header does not use the module."
- [!4045](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4045) mwestphal, 2018-04-03: "this could go into PRIVATE_DEPENDS"

### R082: Remove unused includes and sort them all.

Rationale: The reviewers stated that unused includes should be removed to keep the code clean.

- Scope: all C++ sources
- Support: 5 MRs, 5 threads, 2017-11-23 to 2025-11-19
- Reviewers: jpouderoux (2), mwestphal (2), michael.migliore (1)
- [!12611](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12611) mwestphal, 2025-11-19: "please cleanup and organise includes"
- [!12056](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12056) mwestphal, 2025-04-14: "You can remove this include. Please cleanup all includes as needed :smile:"
- [!4019](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4019) jpouderoux, 2018-03-07: "Please remove all useless include files for those tests."

### R121: Optional dependencies should be treated as private dependencies and not listed as optional in function signatures.

Rationale: Optional dependencies are always treated as private and must be processed with private modules to avoid missing include directories and undefined macros.

- Scope: CMake module files
- Support: 4 MRs, 4 threads, 2021-11-19 to 2025-08-05
- Reviewers: ben.boeckel (3), ryan.krattiger1 (1)
- [!12251](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12251) ben.boeckel, 2025-08-05: "These should never be "optional", so this can be removed. Might be better to do this in an optional-specific loop to gather the "enabled" optional modules then process optional and private together si"
- [!10898](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10898) ben.boeckel, 2024-03-12: "Optional deps are always treated as private if they exist."
- [!9549](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9549) ben.boeckel, 2022-11-15: "This is wrong. `#ifdef` is not right because it is *always* defined. It is instead, a value or `0` or `1`. However, optional dependencies are always private, so code including `vtkGenericDataArray.h` "

### R126: Skip full CI for changes that only affect the Documentation directory.

*Mixed evidence: check the examples before accepting.*

Rationale: Builds are not useful and waste cycles when only documentation is changed.

- Scope: Documentation directory
- Support: 3 MRs, 3 threads, 2015-06-13 to 2025-11-20
- Reviewers: utkarsh.ayachit (1), jcfr (1), mwestphal (1)
- [!12638](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12638) mwestphal, 2025-11-20: "only if in the `doc` directory."
- [!10427](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10427) jcfr, 2023-09-22: "The following rules are intended to include all files and directories expect the `Documentation` directory."
- [!304](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/304) utkarsh.ayachit, 2015-06-13: "BTW, there's no need to trigger buildbot builds when the change is only to documentation. The builds are not going to be of any use in those cases, and will only end up wasting build cycles."
- Counter-evidence:
  - [!10164](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10164) christos.tsolakis, 2023-05-26: "Unfortunately no, passing builds are required even for documentation-only changes. There is a way to bypass that but it is meant only for very urgent situations."

### R138: Use VTK::TestingCore instead of VTK::TestingRendering when only test utilities are needed and configure with VTK_BUILD_TESTING set ON

*Mixed evidence: check the examples before accepting.*

Rationale: VTK::TestingRendering is unnecessary for tests that only compare datasets and need access to the data root via vtkTestUtilities::GetDataRoot

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2023-04-26 to 2025-12-09
- Reviewers: jcfr (1), ben.boeckel (1), lucas.givord (1)
- [!12699](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12699) lucas.givord, 2025-12-09: "VTK::TestingRendering seems useless here because in our test we only compare dataset It is necessary to include vtkTesting in order to have the path to data root Got it, but there is a way to avoid th"
- [!11796](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11796) ben.boeckel, 2024-12-31: "moved to `VTK::TestingCore` with `INTERFACE` visibility"
- [!10163](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10163) jcfr, 2023-04-26: "suggestion 1. Configure with VTK_BUILD_TESTING set ON"
- Counter-evidence:
  - [!7431](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7431) seanm, 2022-04-13: "Use `VTK_BUILD_TESTING=DEFAULT`."

### R144: Avoid whitespace changes and use 2-space indentation with no hard tabs.

Rationale: Whitespace changes pollute history, slow reviews, and break style guides, and hard tabs must be converted to spaces.

- Scope: all C++ sources
- Support: 3 MRs, 3 threads, 2015-08-18 to 2018-03-22
- Reviewers: ben.boeckel (1), dgobbi (1), demarle (1)
- [!4099](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4099) demarle, 2018-03-22: "Try to avoid whitespace changes, they pollute the history, make it take longer to review, and usually break VTK's style guides."
- [!1263](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1263) dgobbi, 2016-02-24: "Hard tabs are not allowed in the VTK code repository, they must be converted to the correct number of spaces."
- [!495](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/495) ben.boeckel, 2015-08-18: "VTK also uses 2-space indentation. Please replace your tabs (kwrobot will not allow the branch otherwise)."

### R147: Use stack-allocated raw arrays or std::vector instead of introducing new stack vector classes or variable-sized stack arrays to avoid maintenance cost and compiler compatibility issues.

Rationale: Introducing new stack vector classes or variable-sized stack arrays increases maintenance cost and may cause compiler compatibility issues, especially with MSVC.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2017-01-13 to 2021-02-10
- Reviewers: alliepiper16 (1), michael.migliore (1), cory.quammen (1)
- [!7600](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7600) cory.quammen, 2021-02-10: "When weighing wether to introduce a new data structure like vtkStackVector, it's important to consider the cost of maintenance of the new class with the performance improvement it offers. In most case"
- [!6240](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6240) michael.migliore, 2019-12-12: "Why the points are allocated on the heap? It looks that this cannot be nullptr, so stack variables looks better to me."
- [!2335](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2335) alliepiper16, 2017-01-13: "This is the problem -- MSVC doesn't support C99 in it's C++ compiler, and variable sized stack arrays are one of the missing features. This is why the original implementation jumped through hoops to u"

### R158: Call Modified() only when the method has an effect.

Rationale: The reviewers stated that Modified() should only be called when its value is actually changed, i.e., when the method has an effect.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2018-04-09 to 2022-08-16
- Reviewers: ben.boeckel (2), dcthomp (1)
- [!9101](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9101) ben.boeckel, 2022-08-16: "Without `Modified()`, there is zero reason to check `!=` before setting."
- [!7516](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7516) ben.boeckel, 2022-05-21: "This is always called. The standard pattern is to only call it if its value is actually changed."
- [!4170](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/4170) dcthomp, 2018-04-09: "On a lot of these, it would be better to ensure that `this->Modified()` is only called when the method has an effect. For example, check the return value of `this->BlockPickabilities.erase(data_object"

### R163: Do not use top-level cache variables named VTK_* in VTK module system code; instead, pass the value as an argument to vtk_module_build().

Rationale: The reviewers stated that VTK module code should never have a cache variable at the top level, especially not named VTK_*, and that the value should be provided via an argument to vtk_module_build().

- Scope: CMake module files
- Support: 3 MRs, 3 threads, 2019-02-05 to 2023-05-25
- Reviewers: ben.boeckel (1), svenevs (1), mwestphal (1)
- [!10200](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10200) mwestphal, 2023-05-25: "ben.boeckel: "No. `vtkModule` should *never* have a cache variable at the top-level (certainly not named `VTK_*`). This should be an argument to `vtk_module_build()` that VTK passes in the value of so"
- [!9541](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9541) svenevs, 2022-09-19: "they should be set(CACHE STRING not INTERNAL"
- [!5132](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5132) ben.boeckel, 2019-02-05: "When a variable is unconditionally set, I've been factoring out the `vtk_module_definitions` and using a variable for the value. Just a nit though."

## api-usage

### R050: Use SafeDownCast for downcasting VTK objects in C++ code.

*Mixed evidence: check the examples before accepting.*

Rationale: SafeDownCast is preferred for consistency and to avoid the performance cost of virtual function calls and string comparisons made by reinterpret_cast or dynamic_cast.

- Scope: C++ sources
- Support: 6 MRs, 7 threads, 2020-08-19 to 2023-09-18
- Reviewers: charles.gueunet (2), tiffany.chhim (2), utkarsh.ayachit (1), timothee.chabat (1), finetjul (1)
- [!8627](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8627) tiffany.chhim, 2021-11-10: "This gets called roughly once per actor per eye pre render. So it can get called a lot. SafeDownCast costs CPU time as it makes a virtual function call and then does a string comparison which will usu"
- [!8303](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8303) finetjul, 2021-09-08: "Use safedowncast instead of reinterpret_cast"
- [!7774](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7774) timothee.chabat, 2021-03-23: "I wanted to make the code more readable by moving the "SafeDownCast" in the callee instead of polluting the read flow before the the call to MergeGhostArray."
- Counter-evidence:
  - [!1453](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1453) alliepiper16, 2016-04-25: "Performance -- `SafeDownCast` can be really expensive depending on how deep the inheritance hierarchy is. Might as well just use `static_cast` when not checking the return value."
  - [!5439](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5439) jpouderoux, 2019-04-18: "smartpointers are useless here"
  - [!5584](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5584) mwestphal, 2019-05-28: "You should be able to use vtkPolyData::GetData instead"

### R063: Virtual methods should be declared virtual in the header and have concrete implementations in subclasses, and should be removed if no class currently overrides them.

Rationale: Reviewers stated that virtual methods must be virtual in base classes when derived classes override them to add functionality, and should be removed if no class currently overrides them.

- Scope: C++ sources
- Support: 6 MRs, 7 threads, 2018-01-16 to 2024-11-12
- Reviewers: mwestphal (3), ben.boeckel (2), michael.migliore (1), francois.mazen (1)
- [!10356](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10356) ben.boeckel, 2023-08-17: "At a minimum, vtkStringArray, vtkFloatArray, vtkDoubleArray."
- [!8897](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8897) ben.boeckel, 2022-02-14: "Yes it has to be virtual: vktObjectBase doesn't know about the ObjectName and just returns the class name and pointer like before. the vtkObject override adds the ObjectName if it is set. vtkObjectBas"
- [!7951](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7951) francois.mazen, 2021-05-25: "Yes, please remove it as there is no need for this now and in the near future."

### R085: Add const to parameters and pointer parameters when they are not modified or constness is implied.

Rationale: Reviewers stated that const qualifiers should be added to indicate parameters are not modified and to improve consistency in newer code.

- Scope: C++ sources
- Support: 5 MRs, 5 threads, 2018-06-25 to 2024-06-25
- Reviewers: dgobbi (2), utkarsh.ayachit (1), ben.boeckel (1), jaswant.panchumarti (1)
- [!11261](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11261) jaswant.panchumarti, 2024-06-25: "ditto, can this be `const`?"
- [!10510](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10510) dgobbi, 2023-09-15: "Add `const FunctionInfo* theFunc` (ditto for header file)."
- [!9499](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9499) ben.boeckel, 2023-01-03: "Can it be `const*` then? Sure. Done."

### R093: Replace GetVoidPointer with GetVariantValue in vtkAbstractArray and use vtkAbstractArray for array access patterns.

*Mixed evidence: check the examples before accepting.*

Rationale: To avoid deep copy and warnings when accessing array data.

- Scope: vtkAbstractArray
- Support: 4 MRs, 4 threads, 2016-03-09 to 2025-10-23
- Reviewers: alliepiper16 (2), charles.gueunet (1), mwestphal (1)
- [!12403](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12403) mwestphal, 2025-10-23: "b56a6b54c7 vtkAbstractArray: Replace GetVoidPointer with GetVariantValue"
- [!5974](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5974) alliepiper16, 2019-09-11: "Calling `GetPointer` on a VTK SOA array will always trigger a deep copy and print a warning. Use `GetComponentArrayPointer` instead."
- [!1315](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/1315) alliepiper16, 2016-03-09: "Use `vtkDataArrayAccessor<ArrayType>::APIType` instead of `ArrayType::ValueType`."
- Counter-evidence:
  - [!6619](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6619) dcthomp, 2020-03-24: "Nothing uses `vtkImageData::GetArrayPointer()` except vtkImageData itself? Even so, we should not remove `vtkImageData::GetArrayPointer()` without deprecating it for a release first."

### R109: Use vtkArrayDispatch to access data arrays as fast as possible to enable fewer virtual function calls and compiler optimizations.

Rationale: It enables automatic dispatching and fallback handling without extra codegen.

- Scope: C++ sources
- Support: 4 MRs, 5 threads, 2019-11-12 to 2021-09-03
- Reviewers: alliepiper16 (3), cory.quammen (2)
- [!8379](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8379) cory.quammen, 2021-09-03: "We should still use `vtkArrayDispatch` to access data arrays as fast as possible. You can either do this inside the `operator()` in the functor or do the array dispatch in `RequestData()`."
- [!6200](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6200) alliepiper16, 2019-11-27: "The `Dispatch3BySameValueType` dispatcher should be used here. It will handle these edge cases without doing a ton of extra codegen, and fail gracefully for arrays it doesn't know about."
- [!6201](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6201) alliepiper16, 2019-11-20: "Fallbacks are practically free :) vtkVectorNormDispatch{}(ptVectors, this, numVectors, newScalars->GetPointer(0)); instead of the error macro will just generate one extra instance of the functor's cal"

### R128: Use vtkSetEnumMacro and vtkGetEnumMacro for enum types instead of vtkSetMacro and vtkGetMacro, and use typedef for enums in VTK codebase.

*Mixed evidence: check the examples before accepting.*

Rationale: To avoid breaking APIs and to properly support enum classes.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2017-06-02 to 2024-06-28
- Reviewers: mwestphal (1), ben.boeckel (1), michael.migliore (1)
- [!11267](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11267) michael.migliore, 2024-06-28: "vtkSetMacro does not support enum class"
- [!8832](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8832) ben.boeckel, 2022-01-24: "Since we're breaking APIs anyways here, why not use `vtkSetEnumMacro` and `vtkGetEnumMacro`?"
- [!2906](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2906) mwestphal, 2017-06-02: "I would suggest : ``` typedef enum vtkQuaternionInterpolationSearchMethod{ BINARY_SEARCH = 0, LINEAR_SEARCH = 1, INTERPOLATION_SEARCH_METHOD_MAX_ENUM } vtkQuaternionInterpolationSearchMethod; ```"
- Counter-evidence:
  - [!12228](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12228) lucas.givord, 2025-07-04: "using an enum class require to deprecate hundreds of methods in `Common/DataModel` which is unrealistic for VTK devs as well as VTK users."

### R135: Pass output parameters by reference rather than pointer.

*Mixed evidence: check the examples before accepting.*

Rationale: To fit with the previous code and avoid expecting null pointers.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2020-03-09 to 2024-06-06
- Reviewers: jpouderoux (1), lassoan (1), lucas.givord (1)
- [!11199](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11199) lucas.givord, 2024-06-06: "to fit with the previous code, we should pass fileID in reference"
- [!7790](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7790) lassoan, 2021-03-26: "Do you expect to get numberOfNodes==nullptr? If not then use int &numberOfNodes."
- [!6551](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6551) jpouderoux, 2020-03-09: "looks like you could directly use outPtr instead as it is not given as a reference"
- Counter-evidence:
  - [!7624](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7624) LucasGandelKitware, 2021-02-18: "This is sent by copy, out is (0,0) when returning from the fonction. Use pointers instead."

### R139: Use vtkArrayDownCast for array retrieval instead of SafeDownCast.

*Mixed evidence: check the examples before accepting.*

Rationale: vtkArrayDownCast is more efficient and performs the safe downcast automatically.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2021-10-27 to 2023-07-06
- Reviewers: yohann.bearzi (1), charles.gueunet (1), charly.bollinger (1)
- [!9346](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9346) charles.gueunet, 2022-07-12: "for data array, you may privilege the more efficient vtkArrayDownCast"
- [!8567](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8567) yohann.bearzi, 2021-10-27: "For arrays, `vtkArrayDownCast<ArrayType>` is a better alternative to the `SafeDownCast`."
- [!10302](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10302) charly.bollinger, 2023-07-06: suggested `vtkDataArray* array = pointData->GetArray(idx); This does the safe downcast for you (and use the `vtkArrayDownCast` for faster conversion when possible)`
- Counter-evidence:
  - [!9812](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9812) julien.fausty, 2023-04-20: "I assumed that there is a coherence between data arrays inside the vtkCellArray container and thus no failures are expected."

### R154: Use GetNumberOfTuples() for VTK arrays, not GetSize()

Rationale: GetSize() means something different for VTK arrays.

- Scope: VTK arrays
- Support: 3 MRs, 3 threads, 2017-06-26 to 2025-08-12
- Reviewers: utkarsh.ayachit (2), dgobbi (1)
- [!11986](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11986) dgobbi, 2025-08-12: "Shouldn't this use `GetNumberOfTuples()`? For VTK arrays, `GetSize()` means something different."
- [!5446](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5446) utkarsh.ayachit, 2019-04-23: "minor suggestion for cleanup here. `vtkDataObject::GetNumberOfElements` is new API. I'd recommend changing this override implementation to iterate over the blocks using iterator and then call `iter->G"
- [!2965](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/2965) utkarsh.ayachit, 2017-06-26: "Then simply call vtkDataObject::GetNumberOfElements(attributeType). No need for the explicit if/else."

## python-wrapping

### R080: Use vtkSmartPointer::Take or vtkSmartPointer::TakeReference to transfer ownership of VTK objects without copying.

Rationale: To avoid copying to an already existing smart pointer.

- Scope: C++ sources
- Support: 5 MRs, 5 threads, 2017-01-10 to 2025-01-28
- Reviewers: dgobbi (1), mwestphal (1), julien.fausty (1), leon.victor (1), cory.quammen (1)
- [!11750](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11750) cory.quammen, 2025-01-28: "This was using the old style before it got replaced with `vtk::TakeSmartPointer`. Just didn't do that consistently."
- [!11361](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11361) leon.victor, 2024-08-13: "Use `vtkSmartPointer::Take` or `vtkSmartPointer::TakeReference` to avoid copying to an already existing smart ptr"
- [!10443](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10443) julien.fausty, 2023-08-28: "error: use of deleted function ‘void vtkSmartPointer<ArrayType>::TakeReference(const vtkSmartPointerBase&) [with T = vtkDataArray]’ 653 | array.TakeReference(vtkSmartPointer<vtkDoubleArray>::New()); a"

### R086: Use emplace_back instead of push_back when constructing or inserting elements into a vector.

Rationale: emplace_back can require less overhead to accomplish the same task as push_back.

- Scope: C++ sources
- Support: 5 MRs, 6 threads, 2019-04-17 to 2023-02-27
- Reviewers: charles.gueunet (3), michael.migliore (1), seanm (1), timothee.chabat (1)
- [!9363](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9363) timothee.chabat, 2022-07-11: "use `emplace_back` instead of `push_back`"
- [!6779](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6779) seanm, 2020-04-21: "emplace_back and push_back have the same effect on sample_values, but emplace_back can require less overhead to accomplish the same task."
- [!5377](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5377) michael.migliore, 2019-04-17: "Use `emplace_back` instead and be sure the object is supporting move constructor to avoid a copy. Here and everywhere is this method."

### R112: Use vtkSetStringMacro and vtkGetStringMacro for string member variables to handle memory management automatically.

Rationale: The reviewers stated that these macros handle memory management automatically.

- Scope: C++ sources
- Support: 4 MRs, 4 threads, 2020-04-09 to 2025-03-28
- Reviewers: utkarsh.ayachit (1), cory.quammen (1), francois.mazen (1), jaswant.panchumarti (1)
- [!9643](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9643) francois.mazen, 2022-10-25: "The `vtkSetStringBodyMacro` frees the memory"
- [!7867](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7867) cory.quammen, 2021-04-25: "char* LevelMaskArrayName = nullptr;"
- [!6621](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6621) utkarsh.ayachit, 2020-04-09: "this method is still weird :). Okay, here's an approach that's more VTK-esque. ```c++ /// in header public: ... vtkSetStringMacro(ActiveTimeArray); vtkGetStringMacro(ActiveTimeArray); protected: char*"

### R137: Remove parameters that are not used in a function signature.

*Mixed evidence: check the examples before accepting.*

Rationale: Unused parameters cause compiler warnings and are unnecessary.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2020-11-05 to 2023-03-08
- Reviewers: cory.quammen (1), ken-martin (1), thomas.galland (1)
- [!10032](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10032) thomas.galland, 2023-03-08: "correct but as we discuss we don't really need this parameter, I removed it"
- [!8608](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8608) ken-martin, 2021-11-08: "This has added compiler warnings to master's build"
- [!7375](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7375) cory.quammen, 2020-11-05: "Consider removing `countReal` since it is not used in `ClassifyDetailed2D` or `ClassifyDetailed3D`."
- Counter-evidence:
  - [!8306](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8306) utkarsh.ayachit, 2021-08-20: "this is failing to build in debug builds now."

### R175: Use vtk_module_test_data() without arguments for C++ test data directories and use vtkTestUtilities::ExpandDataFileName for test data paths.

Rationale: To ensure test data is found by tests and to avoid manual argument parsing.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2020-07-13 to 2023-09-01
- Reviewers: utkarsh.ayachit (1), aangelos28 (1), julien.fausty (1)
- [!7181](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7181) aangelos28, 2020-09-07: "See the `vtk_module_test_data` calls in the tree."
- [!7101](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7101) utkarsh.ayachit, 2020-07-13: "don't parse arguments like so. Instead use `vtkTestUtilities::ExpandDataFileName`. See `TestIossExodus.cxx` for a example."
- [!10459](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10459) julien.fausty, 2023-09-01: suggested `if (NOT vtk_testing_cxx_disabled) vtk_module_test_data() add_subdirectory(Cxx) endif ()`

### R180: Do not add new instances of vtkStdString; use std::string instead.

Rationale: Because std::string is always better and avoids forcing internal storage.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2021-05-12 to 2022-08-29
- Reviewers: ben.boeckel (2), lassoan (1)
- [!9398](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9398) ben.boeckel, 2022-08-29: "Please do not add new instances of `vtkStdString`. `std::string` is always better."
- [!8897](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8897) lassoan, 2022-02-14: "Returning const std::string& would force the implementation of this class to store an std::string internally forever. Therefore, in libraries that offer stable API in the long term the best practice i"
- [!7907](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/7907) ben.boeckel, 2021-05-12: "Please just use `std::string`. New uses of `vtkStdString` should be avoided."

### R194: Do not apply VTK_MARSHALAUT unless marshalling is enabled for the module, and use VTK_MARSHALEXCLUDE with a descriptive reason to exclude internal properties from serialization.

Rationale: To prevent naive (de)serialization issues and ensure explicit, less error-prone exclusion of internal properties.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2024-03-26 to 2024-12-18
- Reviewers: jcfr (1), jaswant.panchumarti (1), cory.quammen (1)
- [!11750](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11750) cory.quammen, 2024-12-18: "Removed. This accidentally slipped in. We did not enable marshalling yet for webgpu module."
- [!11326](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11326) jaswant.panchumarti, 2024-07-22: "let's not expose `Initialized` as a property. Otherwise, the serialization tests will naively (de)serialize the property and as a result the deserializer side will skip initialization for render windo"
- [!10898](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10898) jcfr, 2024-03-26: "After looking at the implementation of the macro ... I then realized it was the "reason", so `VTK_MARSHAL_REASON_IS_INTERNAL` or `VTK_MARSHAL_EXCLUDE_REASON_IS_INTERNAL` would indeed be more explicit "

## docs-release-notes

### R065: Use a proper Doxygen block comment in the code.

Rationale: The reviewers stated that code should include a proper Doxygen block comment.

- Scope: C++ sources
- Support: 6 MRs, 6 threads, 2018-05-24 to 2025-11-10
- Reviewers: mwestphal (2), charles.gueunet (2), jpouderoux (1), michael.migliore (1)
- [!12602](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12602) mwestphal, 2025-11-10: "use a proper doxygen block"
- [!10609](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10609) charles.gueunet, 2023-10-23: "doxygen block comment (here and below)"
- [!6567](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6567) michael.migliore, 2020-03-24: "use doxygen style comments"

### R066: Do not use a doxygen group when there is a single method.

Rationale: Reviewers stated that a doxygen group is unnecessary for a single method.

- Scope: C++ sources
- Support: 6 MRs, 6 threads, 2019-04-16 to 2025-12-10
- Reviewers: mwestphal (4), jpouderoux (1), lucas.givord (1)
- [!12664](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12664) mwestphal, 2025-12-10: "When there is a single method, it is not needed."
- [!9763](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9763) lucas.givord, 2023-03-10: "missing ` ///@}` here to avoid bad doxygen generation"
- [!9602](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9602) mwestphal, 2022-11-23: "doxygen group not needed"

### R173: Add a copyright and SPDX license header to the start of new files.

Rationale: Reviewers stated that new files must include a copyright header and SPDX license identifier.

- Scope: new files
- Support: 3 MRs, 3 threads, 2020-05-27 to 2025-09-16
- Reviewers: ben.boeckel (1), mwestphal (1), timothee.couble (1)
- [!12459](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12459) timothee.couble, 2025-09-16: "// SPDX-FileCopyrightText: Copyright (c) Kitware Inc. // SPDX-FileCopyrightText: Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen // SPDX-License-Identifier: BSD-3-Clause"
- [!9369](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9369) mwestphal, 2022-07-08: "Add standard license headers to all files"
- [!6917](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6917) ben.boeckel, 2020-05-27: "Copyright header"

## correctness

### R064: Check for nullptr before dereferencing or passing to other methods to prevent undefined behavior or unintended state changes.

Rationale: To prevent undefined behavior or unintended state changes.

- Scope: C++ sources
- Support: 6 MRs, 7 threads, 2018-01-11 to 2025-05-14
- Reviewers: ken-martin (1), sebastien.jourdain (1), ben.boeckel (1), mwestphal (1), tiffany.chhim (1)
- [!12106](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12106) shreeraj.jadhav, 2025-05-14: "Do we need a `nullptr` check on any of the input parameters? Or do we expect them to be checked already in the call tree?"
- [!10509](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10509) thomas.galland, 2023-09-19: "Check for `nullptr` (can be)"
- [!9468](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9468) mwestphal, 2022-10-04: "`if (frequencies)` should be enough ?"

## threading-smp

### R132: Use vtkSMPTools::For and vtkSMPTools::Sort to thread loops and sorting when not already in a threaded function.

*Mixed evidence: check the examples before accepting.*

Rationale: The reviewers stated that vtkSMPTools should be used for threading computations as a basic requirement.

- Scope: C++ sources
- Support: 3 MRs, 4 threads, 2021-08-05 to 2023-01-06
- Reviewers: timothee.chabat (3), will.schroeder (1)
- [!9821](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9821) timothee.chabat, 2023-01-06: "There is a few loops / sorts that could be SMP-fied (vtkSMPTools::For, vtkSMPTools::Sort), except if we already are in a threaded function"
- [!8182](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8182) will.schroeder, 2021-08-05: "As you can see from the code, I already use vtkSMPTools for threading. Multithreading was one of the basic requirements that @cory.quammen gave me while I was researching for the best possible mathema"
- [!9232](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9232) timothee.chabat, 2022-06-07: "consider using vtkSMPTools::For"
- Counter-evidence:
  - [!5590](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/5590) will.schroeder, 2019-05-31: "BTW the serial processing means instead of calling vtkSMPTools::For(), you have to manually call Initialize(), then functor(begin,end), then Reduce(). This is controlled by the serial flag."

### R168: Use vtkSMPThreadLocalObject for thread-local instances of classes like vtkLabelMapLookup in SMP contexts and remove manual lifecycle management.

Rationale: To enable safe use in SMP parallel contexts and avoid manual lifecycle management.

- Scope: C++ sources
- Support: 3 MRs, 3 threads, 2019-12-16 to 2024-05-30
- Reviewers: michael.migliore (1), charles.gueunet (1), will.schroeder (1)
- [!11177](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/11177) will.schroeder, 2024-05-30: "Spiros is correct, the vtkLabelMapLookup is meant to be used as a vtkSMPThreadLocal variable."
- [!10750](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10750) charles.gueunet, 2023-12-13: "To use this class in a smp parallel context, one has to create one instance per thread, using a `vtkSMPThreadLocal`."
- [!6240](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6240) michael.migliore, 2019-12-16: "Use `vtkSMPThreadLocalObject` where you can and remove manual life cycle management"

## testing

### R166: Test availability of the vtk_temp_dir before using it.

Rationale: Tests should use vtkTesting::GetTempDirectory to avoid failures on Windows.

- Scope: tests
- Support: 3 MRs, 3 threads, 2019-10-28 to 2023-07-21
- Reviewers: chuck.atkins (1), ben.boeckel (1), lucas.givord (1)
- [!10330](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/10330) lucas.givord, 2023-07-21: "test availablity of the vtk_temp_dir before using it (so check that tempDir isn't null)"
- [!6304](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6304) ben.boeckel, 2019-12-23: "Tests should use `vtkTesting::GetTempDirectory`. This is going to fail on Windows otherwise."
- [!6084](https://gitlab.kitware.com/vtk/vtk/-/merge_requests/6084) chuck.atkins, 2019-10-28: "All files written by tests should be rooted under the `-T` directory (see `vtkTesting::GetTempDirectory()`)."
