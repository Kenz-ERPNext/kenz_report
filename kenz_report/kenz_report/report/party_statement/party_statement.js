frappe.query_reports["Party Statement"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "customer_group",
			label: __("Customer Group"),
			fieldtype: "Link",
			options: "Customer Group",
		},
		{
			fieldname: "territory",
			label: __("Territory"),
			fieldtype: "Link",
			options: "Territory",
		},
		{
			fieldname: "sales_person",
			label: __("Sales Person"),
			fieldtype: "Link",
			options: "Sales Person",
		},
		{
			fieldname: "show_only_with_balance",
			label: __("Only Customers with Balance"),
			fieldtype: "Check",
			default: 0,
		},
	],

	onload(report) {
		report.page.add_inner_button(__("Print Statement"), () => {
			const filters = report.get_values();
			frappe.call({
				method: "kenz_report.api.party_statement.print_statement",
				args: { filters },
				callback(r) {
					if (!r.message || !r.message.html) return;
					const w = window.open("", "_blank");
					w.document.write(r.message.html);
					w.document.close();
					w.focus();
					setTimeout(() => w.print(), 500);
				},
			});
		});
	},

	formatter(value, row, column, data, default_formatter) {
		if (data && (data.is_opening || data.is_closing)) {
			value = default_formatter(value, row, column, data);
			return `<b>${value}</b>`;
		}
		if (data && data.is_group_header) {
			value = default_formatter(value, row, column, data);
			return `<span style="background:#eef; font-weight:bold">${value}</span>`;
		}
		return default_formatter(value, row, column, data);
	},
};
