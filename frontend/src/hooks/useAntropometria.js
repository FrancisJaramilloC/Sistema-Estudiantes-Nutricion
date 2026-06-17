import { useMemo } from 'react';

function calcularIMC(peso_kg, estatura_m) {
  if (!peso_kg || !estatura_m || estatura_m <= 0) return null;
  return parseFloat((peso_kg / (estatura_m ** 2)).toFixed(2));
}

function clasificarIMC(imc) {
  if (imc === null) return null;
  if (imc < 18.5) return 'Bajo peso';
  if (imc < 25.0) return 'Normal';
  if (imc < 30.0) return 'Sobrepeso';
  return 'Obesidad';
}

function obtenerColorIMC(clasificacion) {
  switch (clasificacion) {
    case 'Normal': return '#16a34a';
    case 'Bajo peso': return '#fbbf24';
    case 'Sobrepeso': return '#ea580c';
    case 'Obesidad': return '#dc2626';
    default: return '#78716c';
  }
}

function calcularICC(perimetro_cintura_cm, perimetro_cadera_cm) {
  if (!perimetro_cintura_cm || !perimetro_cadera_cm || perimetro_cadera_cm <= 0) return null;
  return parseFloat((perimetro_cintura_cm / perimetro_cadera_cm).toFixed(2));
}

function clasificarICC(icc, sexo_biologico) {
  if (icc === null) return { riesgo: null, distribucion: null };
  const sex = sexo_biologico?.trim().toLowerCase() || 'masculino';

  if (sex === 'masculino' || sex === 'm') {
    if (icc <= 0.90) return { riesgo: 'Bajo', distribucion: 'Ginecoide (Pera)' };
    if (icc <= 0.95) return { riesgo: 'Moderado', distribucion: 'Ginecoide (Pera)' };
    return { riesgo: 'Alto', distribucion: 'Obesidad Androide (Manzana)' };
  }

  if (icc <= 0.80) return { riesgo: 'Bajo', distribucion: 'Ginecoide (Pera)' };
  if (icc <= 0.85) return { riesgo: 'Moderado', distribucion: 'Ginecoide (Pera)' };
  return { riesgo: 'Alto', distribucion: 'Obesidad Androide (Manzana)' };
}

function obtenerColorICC(riesgo) {
  switch (riesgo) {
    case 'Bajo': return '#16a34a';
    case 'Moderado': return '#fbbf24';
    case 'Alto': return '#dc2626';
    default: return '#78716c';
  }
}

function calcularTMBHarris(peso_kg, estatura_m, edad, sexo_biologico) {
  const estatura_cm = estatura_m * 100;
  const sex = sexo_biologico?.trim().toLowerCase() || 'masculino';
  if (sex === 'masculino' || sex === 'm') {
    return parseFloat((66.47 + (13.75 * peso_kg) + (5.0 * estatura_cm) - (6.76 * edad)).toFixed(2));
  }
  return parseFloat((655.10 + (9.56 * peso_kg) + (1.85 * estatura_cm) - (4.68 * edad)).toFixed(2));
}

function calcularTMBMifflin(peso_kg, estatura_m, edad, sexo_biologico) {
  const estatura_cm = estatura_m * 100;
  const sex = sexo_biologico?.trim().toLowerCase() || 'masculino';
  if (sex === 'masculino' || sex === 'm') {
    return parseFloat(((10.0 * peso_kg) + (6.25 * estatura_cm) - (5.0 * edad) + 5.0).toFixed(2));
  }
  return parseFloat(((10.0 * peso_kg) + (6.25 * estatura_cm) - (5.0 * edad) - 161.0).toFixed(2));
}

function calcularGET(tmb, factor_actividad, efecto_termogenico) {
  return parseFloat((tmb * factor_actividad * (1.0 + (efecto_termogenico / 100.0))).toFixed(2));
}

export default function useAntropometria({
  peso_kg,
  estatura_m,
  perimetro_cintura_cm,
  perimetro_cadera_cm,
  sexo_biologico,
  edad,
  factor_actividad,
  efecto_termogenico,
}) {
  return useMemo(() => {
    const imc = calcularIMC(peso_kg, estatura_m);
    const imc_clasificacion = clasificarIMC(imc);
    const imc_color = obtenerColorIMC(imc_clasificacion);

    const icc = calcularICC(perimetro_cintura_cm, perimetro_cadera_cm);
    const { riesgo: icc_riesgo, distribucion: distribucion_grasa } = clasificarICC(icc, sexo_biologico);
    const icc_color = obtenerColorICC(icc_riesgo);

    const tmb_harris = (peso_kg && estatura_m && edad) ? calcularTMBHarris(peso_kg, estatura_m, edad, sexo_biologico) : null;
    const tmb_mifflin = (peso_kg && estatura_m && edad) ? calcularTMBMifflin(peso_kg, estatura_m, edad, sexo_biologico) : null;

    const gasto_total_harris = (tmb_harris && factor_actividad && efecto_termogenico !== undefined)
      ? calcularGET(tmb_harris, factor_actividad, efecto_termogenico) : null;
    const gasto_total_mifflin = (tmb_mifflin && factor_actividad && efecto_termogenico !== undefined)
      ? calcularGET(tmb_mifflin, factor_actividad, efecto_termogenico) : null;

    return {
      imc,
      imc_clasificacion,
      imc_color,
      icc,
      icc_riesgo,
      icc_color,
      distribucion_grasa,
      tmb_harris,
      tmb_mifflin,
      gasto_total_harris,
      gasto_total_mifflin,
    };
  }, [peso_kg, estatura_m, perimetro_cintura_cm, perimetro_cadera_cm, sexo_biologico, edad, factor_actividad, efecto_termogenico]);
}
