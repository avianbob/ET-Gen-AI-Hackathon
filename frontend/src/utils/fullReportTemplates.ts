/**
 * Client-side baseline for process / TEA / demographics (matches backend templates).
 * Used when persisted or legacy payloads omit full_report_extensions.
 */
export type FullReportExtensionsShape = {
  process_design: string;
  techno_economic: string;
  demographics_sites: string;
};

export function buildTemplateFullReportExtensions(
  drugName: string,
  topIndications: string
): FullReportExtensionsShape {
  const drug = drugName?.trim() || 'Unknown';
  const tops = topIndications?.trim() || 'general repurposing hypotheses';
  return {
    process_design:
      `**${drug} — process design (summary)**\n\n` +
      'High-level oral solid or sterile routing depends on API physicochemistry and the target dosage form from labeling and evidence. ' +
      'Apply QbD to tie critical process parameters to dissolution, purity, and stability; align scale-up with GMP expectations for repurposing ' +
      'programs (e.g. 505(b)(2) style filings where applicable).',
    techno_economic:
      `**${drug} — techno-economics (indicative)**\n\n` +
      'Order-of-magnitude COGS is driven by batch scale, yield, solvent recovery, and packaging choices. ' +
      'Full business cases should layer in clinical stage, pricing, and share assumptions using the market and competition signals from this search—not investment advice.',
    demographics_sites:
      `**${drug} — demographics & manufacturing footprint**\n\n` +
      `Opportunity themes from this run: **${tops}**. For India-scale supply, clusters such as Hyderabad, Ahmedabad, or Vizag often balance API synergy, talent, and export logistics—` +
      'subject to state incentives, environmental compliance, and target market geography.',
  };
}
