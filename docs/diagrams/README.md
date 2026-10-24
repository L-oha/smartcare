# SmartCare Milestone 3 diagrams
These Mermaid sources are the editable design baseline. The PDF uses drawings rendered from these exact files.

Place this directory at docs/diagrams/ in the existing SmartCare GitHub repository. Review the report and diagrams before committing. Commit the report and diagram sources together, then create the milestone-3 tag on the reviewed commit. No repository upload or tag creation has been performed by generating this package.

Diagram inventory: container; domain and application class views; four sequence scenarios (booking, cancellation, AI success, AI fallback); appointment state; ERD; deployment; AI pipeline.

The ERD shows historical slot-to-appointment cardinality. A separate unique constraint limits confirmed appointments to one per slot. Cancelled records remain in history. Pending selections exist only in the UI.
