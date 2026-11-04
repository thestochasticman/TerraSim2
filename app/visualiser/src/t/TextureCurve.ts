/**
 * One texture's retention curve under one model.
 *
 * texture : the textural class, as the book's tables spell it
 * theta : water content m³/m³, one per suction in the parent's list
 * thetaFc, thetaPwp : water content m³/m³ at field capacity and wilting point
 * availableWater : mm per metre of soil between those two
 */
export type TextureCurve = {
  texture: string;
  theta: number[];
  thetaFc: number;
  thetaPwp: number;
  availableWater: number;
};
