frappe.query_reports["Account Receivable Report"] = {

	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "report_date",
			label: __("Posting Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "finance_book",
			label: __("Finance Book"),
			fieldtype: "Link",
			options: "Finance Book",
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "MultiSelectList",
			options: "Cost Center",
			get_data: function (txt) {
				return frappe.db.get_link_options("Cost Center", txt, {
					company: frappe.query_report.get_filter_value("company"),
				});
			},
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "MultiSelectList",
			options: "Project",
			get_data: function (txt) {
				return frappe.db.get_link_options("Project", txt, {
					company: frappe.query_report.get_filter_value("company"),
				});
			},
		},
		{
			fieldname: "party_type",
			label: __("Party Type"),
			fieldtype: "Autocomplete",
			options: get_party_type_options(),
			on_change: function () {
				frappe.query_report.set_filter_value("party", []);
				frappe.query_report.toggle_filter_display(
					"customer_group",
					frappe.query_report.get_filter_value("party_type") !== "Customer"
				);
			},
		},
		{
			fieldname: "party",
			label: __("Party"),
			fieldtype: "MultiSelectList",
			options: "party_type",
			get_data: function (txt) {
				let party_type = frappe.query_report.get_filter_value("party_type");
				if (!party_type) return [];
				return frappe.db.get_link_options(party_type, txt);
			},
		},
		{
			fieldname: "party_account",
			label: __("Receivable Account"),
			fieldtype: "Link",
			options: "Account",
			get_query: function () {
				return {
					filters: {
						company: frappe.query_report.get_filter_value("company"),
						account_type: "Receivable",
						is_group: 0,
					},
				};
			},
		},
		{
			fieldname: "ageing_based_on",
			label: __("Ageing Based On"),
			fieldtype: "Select",
			options: "Posting Date\nDue Date",
			default: "Due Date",
		},
		{
			fieldname: "calculate_ageing_with",
			label: __("Calculate Ageing With"),
			fieldtype: "Select",
			options: "Report Date\nToday Date",
			default: "Report Date",
		},
		{
			fieldname: "range",
			label: __("Ageing Range"),
			fieldtype: "Data",
			default: "30, 60, 90, 120",
		},
		{
			fieldname: "customer_group",
			label: __("Customer Group"),
			fieldtype: "MultiSelectList",
			options: "Customer Group",
			get_data: function (txt) {
				return frappe.db.get_link_options("Customer Group", txt);
			},
		},
		{
			fieldname: "payment_terms_template",
			label: __("Payment Terms Template"),
			fieldtype: "Link",
			options: "Payment Terms Template",
		},
		{
			fieldname: "sales_partner",
			label: __("Sales Partner"),
			fieldtype: "Link",
			options: "Sales Partner",
		},
		{
			fieldname: "sales_person",
			label: __("Sales Person"),
			fieldtype: "Link",
			options: "Sales Person",
		},
		{
			fieldname: "territory",
			label: __("Territory"),
			fieldtype: "Link",
			options: "Territory",
		},
		{
			fieldname: "group_by_party",
			label: __("Group By Customer"),
			fieldtype: "Check",
		},
		{
			fieldname: "based_on_payment_terms",
			label: __("Based On Payment Terms"),
			fieldtype: "Check",
		},
		{
			fieldname: "show_future_payments",
			label: __("Show Future Payments"),
			fieldtype: "Check",
		},
		{
			fieldname: "show_delivery_notes",
			label: __("Show Linked Delivery Notes"),
			fieldtype: "Check",
		},
		{
			fieldname: "show_sales_person",
			label: __("Show Sales Person"),
			fieldtype: "Check",
		},
		{
			fieldname: "show_remarks",
			label: __("Show Remarks"),
			fieldtype: "Check",
		},
		{
			fieldname: "for_revaluation_journals",
			label: __("Revaluation Journals"),
			fieldtype: "Check",
		},
		{
			fieldname: "ignore_accounts",
			label: __("Group By Voucher"),
			fieldtype: "Check",
		},
		{
			fieldname: "in_party_currency",
			label: __("In Party Currency"),
			fieldtype: "Check",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.bold) {
			value = "<b>" + value + "</b>";
		}
		return value;
	},

	onload: function (report) {

    // Accounts Receivable Summary Button
    report.page.add_inner_button(__("Accounts Receivable Summary"), function () {

        let filters = report.get_values();

        frappe.set_route("query-report", "Accounts Receivable Summary", {
            company: filters.company,
        });

    });


    // // Print Button
    // report.page.add_inner_button(__("Print"), function () {

    //     frappe.call({

    //         method: "kenz_report.api.account_recievable.print_accounts_receivable",

    //         args: {
    //             filters: report.get_values(),
    //         },

    //         callback: function (r) {

    //             if (!r.message) {
    //                 frappe.msgprint("No print data found");
    //                 return;
    //             }

    //             let w = window.open("", "_blank");

    //             w.document.write(r.message.html);
    //             w.document.close();

    //             setTimeout(function () {
    //                 w.print();
    //             }, 500);

    //         }

        // });

    // });


    // Default Ageing Range
    if (frappe.boot.sysdefaults.default_ageing_range) {

        report.set_filter_value(
            "range",
            frappe.boot.sysdefaults.default_ageing_range
        );

    }

},
};

erpnext.utils.add_dimensions("Accounts Receivable", 9);

function get_party_type_options() {
	let options = [];

	frappe.db
		.get_list("Party Type", {
			filters: {
				account_type: "Receivable",
			},
			fields: ["name"],
		})
		.then((r) => {
			r.forEach((d) => {
				options.push(d.name);
			});
		});

	return options;
}