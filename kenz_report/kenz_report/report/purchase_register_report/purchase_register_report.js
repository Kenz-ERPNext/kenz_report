// Copyright (c) 2026, sammish and contributors

frappe.query_reports["Purchase Register Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			width: "80",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
		},
		{
			fieldname: "supplier_group",
			label: __("Supplier Group"),
			fieldtype: "Link",
			options: "Supplier Group",
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "mode_of_payment",
			label: __("Mode of Payment"),
			fieldtype: "Link",
			options: "Mode of Payment",
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
		},
		{
			fieldname: "include_payments",
			label: __("Show Ledger View"),
			fieldtype: "Check",
			default: 0,
		},
	],

	onload(report) {

		report.page.add_inner_button(__("Print"), () => {

			frappe.call({
				method: "kenz_report.api.purchase_register.print_purchase_register",
				args: {
					filters: report.get_values()
				},
				callback(r) {

					if (!r.message) return;

					const win = window.open("", "_blank");

					win.document.write(r.message.html);

					win.document.close();

					setTimeout(() => {
						win.print();
					}, 500);

				}
			});

		});

	},
};

erpnext.utils.add_dimensions("Purchase Register Report", 7);