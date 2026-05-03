/**
 * Zalary Wave 3 viem worker interface.
 */

const WORKER_ROUTES = [
  "GET  /health",
  "POST /payrollvault/create-payroll",
  "POST /payrollvault/upload-allocations",
  "POST /payrollvault/finalize-allocations",
  "POST /payrollvault/fund-payroll",
  "POST /payrollvault/activate-payroll",
  "POST /payrollvault/request-claim",
  "POST /payrollvault/finalize-claim",
  "POST /payrollvault/cancel-claim",
  "POST /swaprouter/request-withdraw",
  "POST /swaprouter/finalize-withdraw",
];

function main() {
  console.log("Zalary Wave 3 viem worker interface");
  console.table(WORKER_ROUTES);
}

main();
